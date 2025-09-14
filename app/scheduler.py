from datetime import datetime
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from .models import JandoyunRecord, ProcessingTask, db
from .jandoyun_service import JandoyunService
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
                records = JandoyunRecord.query.filter_by(processed=False).limit(100).all()
                
                if not records:
                    current_app.logger.info("没有未处理的简道云记录")
                    return
                
                jandoyun_service = JandoyunService()
                external_api_service = ExternalApiService()
                
                for record in records:
                    try:
                        current_app.logger.info(f"处理简道云记录: {record.record_id}")
                        
                        # 这里可以添加业务逻辑处理
                        # 例如，从记录中提取数据，调用外部API进行处理
                        # 然后更新记录状态
                        
                        # 示例：假设我们需要调用外部API处理数据
                        api_result = external_api_service.call_api(
                            endpoint='process_data',
                            method='POST',
                            data=record.data
                        )
                        
                        if api_result:
                            # 更新记录处理状态
                            record.processed = True
                            record.process_result = "处理成功"
                            
                            # 示例：根据API处理结果更新简道云记录
                            update_data = {
                                # 根据实际情况构建更新数据
                                "processed_status": "已处理",
                                "processed_time": datetime.utcnow().isoformat(),
                                "process_result": "处理成功"
                            }
                            jandoyun_service.update_record(record.form_id, record.record_id, update_data)
                        else:
                            record.processed = True
                            record.process_result = "处理失败：外部API调用失败"
                        
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
                    current_app.logger.info(f"外部API轮询成功，获取到 {len(api_result)} 条数据")
                    
                    # 这里可以添加处理逻辑，例如将获取的数据保存到数据库或创建简道云记录
                    jandoyun_service = JandoyunService()
                    
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

# 创建调度器实例
scheduler_manager = SchedulerManager()