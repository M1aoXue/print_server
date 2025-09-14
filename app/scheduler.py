from datetime import datetime
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from .models import JDYRecord, ProcessingTask, db
from .jdy_service import JDYService
from .external_api_service import ExternalApiService

class SchedulerManager:
    def __init__(self, app=None):
        self.scheduler = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化调度器"""
        if self.scheduler is not None:
            return
        
        # 创建后台调度器
        self.scheduler = BackgroundScheduler()
        self.scheduler.app = app
        
        # 添加定时任务
        self._add_jobs()
        
        # 启动调度器
        try:
            self.scheduler.start()
            app.logger.info("定时任务调度器已启动")
        except Exception as e:
            app.logger.error(f"启动定时任务调度器失败: {str(e)}")
    
    def _add_jobs(self):
        """添加定时任务"""
        # 每5分钟检查一次未处理的简道云记录
        self.scheduler.add_job(
            func=self.process_unprocessed_records,
            trigger=IntervalTrigger(minutes=5),
            id='process_unprocessed_records',
            name='处理未处理的简道云记录',
            replace_existing=True
        )
        
        # 每10分钟执行一次外部API轮询
        self.scheduler.add_job(
            func=self.poll_external_api,
            trigger=IntervalTrigger(minutes=10),
            id='poll_external_api',
            name='轮询外部API',
            replace_existing=True
        )
        
        # 每2分钟处理待处理的任务
        self.scheduler.add_job(
            func=self.process_pending_tasks,
            trigger=IntervalTrigger(minutes=2),
            id='process_pending_tasks',
            name='处理待处理的任务',
            replace_existing=True
        )
        
        # 每30秒轮询计算任务结果
        self.scheduler.add_job(
            func=self.poll_calculation_tasks,
            trigger=IntervalTrigger(seconds=30),
            id='poll_calculation_tasks',
            name='轮询计算任务结果',
            replace_existing=True
        )
        
        # 每天凌晨2点清理一周前的API日志
        self.scheduler.add_job(
            func=self.cleanup_api_logs,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_api_logs',
            name='清理API日志',
            replace_existing=True
        )
    
    def process_unprocessed_records(self):
        """处理未处理的简道云记录"""
        with self.scheduler.app.app_context():
            try:
                # 获取未处理的记录
                records = JDYRecord.query.filter_by(processed=False).limit(100).all()
                
                if not records:
                    current_app.logger.info("没有未处理的简道云记录")
                    return
                
                jdy_service = JDYService()
                
                for record in records:
                    try:
                        current_app.logger.info(f"处理简道云记录: {record.record_id}")
                        
                        # 调用业务处理器处理表单数据
                        from .business_processor import BusinessProcessor
                        business_processor = BusinessProcessor()
                        success, result = business_processor.process_form_data(
                            record.form_id,
                            record.record_id,
                            record.data
                        )
                        
                        if success:
                            # 更新记录处理状态
                            record.processed = True
                            record.process_result = "处理成功"
                            
                            # 根据API处理结果更新简道云记录
                            update_data = {
                                "processed_status": "已处理",
                                "processed_time": datetime.utcnow().isoformat(),
                                "process_result": "处理成功"
                            }
                            jdy_service.update_record(record.form_id, record.record_id, update_data)
                        else:
                            record.processed = True
                            record.process_result = f"处理失败：{result}"
                        
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"处理记录 {record.record_id} 失败: {str(e)}")
                        record.processed = True
                        record.process_result = f"处理失败：{str(e)}"
                        db.session.commit()
            except Exception as e:
                current_app.logger.error(f"处理未处理记录任务失败: {str(e)}")
    
    def poll_external_api(self):
        """轮询外部API"""
        with self.scheduler.app.app_context():
            try:
                current_app.logger.info("开始轮询外部API")
                
                external_api_service = ExternalApiService()
                
                # 调用外部API获取数据
                api_result = external_api_service.call_api(
                    endpoint='poll_data',
                    method='GET'
                )
                
                if api_result:
                    current_app.logger.info(f"外部API轮询成功，获取到数据")
                    
                    # 这里可以添加处理逻辑，例如将获取的数据保存到数据库或创建简道云记录
                    jdy_service = JDYService()
                    
                    # 根据实际需求处理获取到的数据
                    if isinstance(api_result, list):
                        current_app.logger.info(f"外部API轮询成功，获取到 {len(api_result)} 条数据")
                        for item in api_result:
                            try:
                                # 创建处理任务
                                task = ProcessingTask(
                                    task_type='external_data_processing',
                                    data=item
                                )
                                db.session.add(task)
                                db.session.commit()
                            except Exception as e:
                                current_app.logger.error(f"创建处理任务失败: {str(e)}")
            except Exception as e:
                current_app.logger.error(f"外部API轮询任务失败: {str(e)}")
    
    def cleanup_api_logs(self):
        """清理一周前的API日志"""
        with self.scheduler.app.app_context():
            try:
                from datetime import timedelta
                
                # 计算一周前的时间
                one_week_ago = datetime.utcnow() - timedelta(days=7)
                
                # 删除一周前的日志
                from .models import ExternalApiLog
                deleted_count = ExternalApiLog.query.filter(ExternalApiLog.created_at < one_week_ago).delete()
                db.session.commit()
                
                current_app.logger.info(f"清理了 {deleted_count} 条一周前的API日志")
            except Exception as e:
                current_app.logger.error(f"清理API日志任务失败: {str(e)}")

    def process_pending_tasks(self):
        """处理待处理的任务"""
        with self.scheduler.app.app_context():
            try:
                # 获取待处理的任务
                tasks = ProcessingTask.query.filter_by(status='pending').order_by(ProcessingTask.priority.asc()).limit(50).all()
                
                if not tasks:
                    current_app.logger.info("没有待处理的任务")
                    return
                
                for task in tasks:
                    try:
                        current_app.logger.info(f"处理任务: {task.id}, 类型: {task.task_type}")
                        
                        # 更新任务状态为处理中
                        task.status = 'processing'
                        db.session.commit()
                        
                        # 根据任务类型进行不同处理
                        if task.task_type == 'form_record_processing':
                            # 处理表单记录
                            form_id = task.data.get('form_id')
                            record_id = task.data.get('record_id')
                            record_data = task.data.get('record_data')
                            
                            if form_id and record_id:
                                from .business_processor import BusinessProcessor
                                business_processor = BusinessProcessor()
                                success, result = business_processor.process_form_data(form_id, record_id, record_data)
                                if success:
                                    task.status = 'completed'
                                    task.data['result'] = result
                                else:
                                    task.status = 'failed'
                                    task.error_message = str(result)
                            else:
                                task.status = 'failed'
                                task.error_message = '缺少表单ID或记录ID'
                                
                        elif task.task_type == 'external_data_processing':
                            # 处理外部数据
                            # 这里可以根据实际需求实现处理逻辑
                            current_app.logger.info(f"处理外部数据: {task.data}")
                            task.status = 'completed'
                            
                        else:
                            # 未知任务类型
                            current_app.logger.warning(f"未知任务类型: {task.task_type}")
                            task.status = 'failed'
                            task.error_message = f'未知任务类型: {task.task_type}'
                        
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"处理任务 {task.id} 失败: {str(e)}")
                        task.status = 'failed'
                        task.error_message = str(e)
                        db.session.commit()
            except Exception as e:
                current_app.logger.error(f"处理待处理任务失败: {str(e)}")
                
    def poll_calculation_tasks(self):
        """轮询计算任务结果"""
        with self.scheduler.app.app_context():
            try:
                from datetime import datetime, timedelta
                
                # 获取处理中的计算任务，且最后更新时间超过轮询间隔
                poll_interval = 30  # 默认轮询间隔30秒
                try:
                    from .config_manager import config_manager
                    poll_interval = config_manager.get_calculation_config()['poll_interval']
                except:
                    pass
                    
                threshold_time = datetime.utcnow() - timedelta(seconds=poll_interval)
                
                tasks = ProcessingTask.query.filter(
                    ProcessingTask.task_type == 'calculation',
                    ProcessingTask.status == 'processing',
                    ProcessingTask.updated_at < threshold_time
                ).limit(50).all()
                
                if not tasks:
                    current_app.logger.info("没有需要轮询的计算任务")
                    return
                
                for task in tasks:
                    try:
                        current_app.logger.info(f"轮询计算任务: {task.id}")
                        
                        # 获取外部任务ID
                        external_task_id = task.data.get('external_task_id')
                        if not external_task_id:
                            current_app.logger.error(f"计算任务 {task.id} 缺少外部任务ID")
                            task.status = 'failed'
                            task.error_message = '缺少外部任务ID'
                            db.session.commit()
                            continue
                        
                        # 轮询计算结果
                        from .business_processor import BusinessProcessor
                        business_processor = BusinessProcessor()
                        success, result = business_processor.poll_calculation_result(external_task_id)
                        
                        if success is not None:
                            # 任务已完成或失败
                            if success:
                                # 任务成功完成
                                task.status = 'completed'
                                task.data['result'] = result
                                
                                # 处理计算结果
                                form_id = task.data.get('form_id')
                                record_id = task.data.get('record_id')
                                if form_id and record_id:
                                    process_success, process_result = business_processor._process_calculation_result(
                                        form_id, record_id, result
                                    )
                                    if not process_success:
                                        current_app.logger.error(f"处理计算结果失败: {process_result}")
                            else:
                                # 任务失败
                                task.status = 'failed'
                                task.error_message = str(result)
                                
                            db.session.commit()
                        else:
                            # 任务仍在处理中，更新时间戳
                            task.updated_at = datetime.utcnow()
                            db.session.commit()
                            current_app.logger.info(f"计算任务 {task.id} 仍在处理中")
                        
                    except Exception as e:
                        current_app.logger.error(f"轮询计算任务 {task.id} 失败: {str(e)}")
                        task.updated_at = datetime.utcnow()
                        db.session.commit()
            except Exception as e:
                current_app.logger.error(f"轮询计算任务失败: {str(e)}")

# 创建调度器实例
scheduler_manager = SchedulerManager()