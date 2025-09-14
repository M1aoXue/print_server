import time
from datetime import datetime, timedelta
import time
from flask import current_app
from .models import db, JDYRecord, ProcessingTask
from .jdy_service import JDYService
from .external_api_service import ExternalApiService
from .wechat_notification_service import WechatNotificationService
from .config_manager import config_manager

class BusinessProcessor:
    """业务处理器，实现核心业务逻辑"""
    
    def __init__(self):
        self.jdy_service = JDYService()
        self.external_api_service = ExternalApiService()
        self.wechat_service = WechatNotificationService()
        self.config = config_manager
    
    def process_form_record(self, form_id, record_id, record_data):
        """处理表单记录"""
        try:
            # 判断是否为需要处理的表单
            if not self.config.is_form_process_required(form_id):
                current_app.logger.info(f"表单 {form_id} 不需要特殊处理，直接保存记录")
                return True, "记录已保存，无需特殊处理"
            
            # 构建处理任务
            task = ProcessingTask(
                task_type='form_record_processing',
                data={
                    'form_id': form_id,
                    'record_id': record_id,
                    'record_data': record_data
                }
            )
            db.session.add(task)
            db.session.commit()
            
            # 异步处理记录（实际处理在调度器中执行）
            current_app.logger.info(f"创建表单记录处理任务: {task.id}")
            
            # 发送企业微信通知
            self.wechat_service.send_text_message(
                content=f"【新记录待处理】\n表单ID: {form_id}\n记录ID: {record_id}\n任务ID: {task.id}"
            )
            
            return True, f"记录已保存，任务ID: {task.id}"
        except Exception as e:
            current_app.logger.error(f"处理表单记录失败: {str(e)}")
            return False, str(e)
    
    def process_flow_complete(self, flow_id, form_id, record_id, flow_data):
        """处理流程完成事件"""
        try:
            # 检查是否为需要监控的流程
            if not self.config.is_flow_monitored(flow_id):
                current_app.logger.info(f"流程 {flow_id} 不需要监控，跳过处理")
                return True, "流程不需要监控"
            
            # 获取流程表单记录
            record = JDYRecord.query.filter_by(record_id=record_id).first()
            if not record:
                # 如果记录不存在，创建新记录
                record = JDYRecord(
                    form_id=form_id,
                    record_id=record_id,
                    data=flow_data
                )
                db.session.add(record)
            else:
                # 更新记录数据
                record.data = flow_data
                record.updated_at = datetime.utcnow()
            
            # 标记为流程已完成
            record.process_result = "流程已完成"
            db.session.commit()
            
            # 发送企业微信通知
            self.wechat_service.send_text_message(
                content=f"【流程已完成】\n流程ID: {flow_id}\n表单ID: {form_id}\n记录ID: {record_id}"
            )
            
            return True, "流程完成处理成功"
        except Exception as e:
            current_app.logger.error(f"处理流程完成事件失败: {str(e)}")
            return False, str(e)
    
    def trigger_calculation_task(self, data):
        """触发计算任务"""
        try:
            # 调用外部API触发计算任务
            calc_config = self.config.get_calculation_config()
            result = self.external_api_service.call_api(
                endpoint=calc_config['endpoint'],
                method='POST',
                data=data
            )
            
            if result and 'task_id' in result:
                task_id = result['task_id']
                current_app.logger.info(f"计算任务已触发，任务ID: {task_id}")
                
                # 创建计算任务记录
                calculation_task = ProcessingTask(
                    task_type='calculation',
                    data={
                        'external_task_id': task_id,
                        'input_data': data
                    },
                    status='processing'
                )
                db.session.add(calculation_task)
                db.session.commit()
                
                return True, task_id
            else:
                current_app.logger.error(f"触发计算任务失败: {result}")
                return False, "触发计算任务失败"
        except Exception as e:
            current_app.logger.error(f"触发计算任务异常: {str(e)}")
            return False, str(e)
    
    def poll_calculation_result(self, task_id):
        """轮询计算任务结果"""
        try:
            calc_config = self.config.get_calculation_config()
            result = self.external_api_service.call_api(
                endpoint=f"{calc_config['poll_endpoint']}/{task_id}",
                method='GET'
            )
            
            if result:
                # 检查任务状态
                if result.get('status') == 'completed':
                    return True, result.get('result', {})
                elif result.get('status') == 'failed':
                    return False, result.get('error', '计算任务失败')
                else:
                    return None, None  # 任务仍在处理中
            else:
                return False, "获取计算结果失败"
        except Exception as e:
            current_app.logger.error(f"轮询计算任务结果异常: {str(e)}")
            return False, str(e)
    
    def process_form_data(self, form_id, record_id, record_data):
        """处理表单数据（复杂逻辑运算）"""
        try:
            # 格式化记录数据
            formatted_data = self._format_record_data(record_data)
            
            # 触发计算任务
            success, task_id = self.trigger_calculation_task(formatted_data)
            if not success:
                return False, task_id
            
            # 轮询计算结果
            calc_config = self.config.get_calculation_config()
            retry_count = 0
            while retry_count < calc_config['max_retries']:
                time.sleep(calc_config['poll_interval'])
                
                success, result = self.poll_calculation_result(task_id)
                if success is not None:
                    if success:
                        # 计算成功，处理结果
                        return self._process_calculation_result(form_id, record_id, result)
                    else:
                        return False, result
                
                retry_count += 1
                current_app.logger.info(f"轮询计算结果中，任务ID: {task_id}, 重试次数: {retry_count}")
            
            return False, "计算任务超时"
        except Exception as e:
            current_app.logger.error(f"处理表单数据异常: {str(e)}")
            return False, str(e)
    
    def create_process_form(self, data):
        """创建流程表单"""
        try:
            # 获取流程表单ID
            process_form_config = self.config.get_form_config('process_form')
            form_id = process_form_config.get('id')
            
            if not form_id:
                return False, "未配置流程表单ID"
            
            # 创建流程表单记录
            result = self.jdy_service.create_record(form_id, data)
            
            if result:
                current_app.logger.info(f"流程表单已创建，记录ID: {result.get('_id')}")
                return True, result.get('_id')
            else:
                return False, "创建流程表单失败"
        except Exception as e:
            current_app.logger.error(f"创建流程表单异常: {str(e)}")
            return False, str(e)
    
    def _format_record_data(self, record_data):
        """格式化记录数据"""
        # 根据实际需求实现数据格式化逻辑
        formatted_data = {}
        
        # 示例：提取需要的字段
        for key, value in record_data.items():
            # 跳过系统字段（以下划线开头的字段）
            if not key.startswith('_'):
                formatted_data[key] = value
        
        return formatted_data
    
    def _process_calculation_result(self, form_id, record_id, result):
        """处理计算结果"""
        try:
            # 1. 更新数据库记录
            record = JDYRecord.query.filter_by(record_id=record_id).first()
            if record:
                # 在记录数据中添加计算结果
                if isinstance(record.data, dict):
                    record.data['calculation_result'] = result
                    record.processed = True
                    record.process_result = "计算完成"
                db.session.commit()
            
            # 2. 创建流程表单
            success, process_record_id = self.create_process_form(result)
            if not success:
                return False, process_record_id
            
            # 3. 发送企业微信通知
            self.wechat_service.send_text_message(
                content=f"【计算任务完成】\n表单ID: {form_id}\n记录ID: {record_id}\n流程表单ID: {process_record_id}\n计算结果摘要: {str(result)[:100]}..."
            )
            
            return True, {"process_record_id": process_record_id, "result": result}
        except Exception as e:
            current_app.logger.error(f"处理计算结果异常: {str(e)}")
            return False, str(e)