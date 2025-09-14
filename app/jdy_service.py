import time
import json
import hmac
import hashlib
import requests
import time
from flask import current_app
from .models import JDYRecord, db

class JDYService:
    def __init__(self):
        self.app_id = current_app.config['JDY_APP_ID']
        self.app_secret = current_app.config['JDY_APP_SECRET']
        self.api_url = current_app.config['JDY_API_URL']
        self.webhook_secret = current_app.config['JDY_WEBHOOK_SECRET']
        self.access_token = None
        self.token_expires_at = 0
    
    def _get_access_token(self):
        """获取简道云访问令牌"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expires_at - 600:  # 提前10分钟刷新
            return self.access_token
        
        url = f"{self.api_url}get_access_token"
        data = {
            "appid": self.app_id,
            "secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result.get('access_token')
                self.token_expires_at = current_time + result.get('expires_in', 7200)
                return self.access_token
            else:
                current_app.logger.error(f"获取简道云访问令牌失败: {result}")
                return None
        except Exception as e:
            current_app.logger.error(f"获取简道云访问令牌异常: {str(e)}")
            return None
    
    def create_record(self, form_id, data):
        """创建简道云表单记录"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.api_url}apps/{form_id}/datas"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "data": data
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                # 保存记录到数据库
                new_record = JDYRecord(
                    form_id=form_id,
                    record_id=result.get('data', {}).get('_id'),
                    data=data
                )
                db.session.add(new_record)
                db.session.commit()
                
                return result.get('data')
            else:
                current_app.logger.error(f"创建简道云记录失败: {result}")
                return None
        except Exception as e:
            current_app.logger.error(f"创建简道云记录异常: {str(e)}")
            return None
    
    def update_record(self, form_id, record_id, data):
        """更新简道云表单记录"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.api_url}apps/{form_id}/datas/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "data": data
        }
        
        try:
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                # 更新数据库中的记录
                record = JDYRecord.query.filter_by(record_id=record_id).first()
                if record:
                    record.data = data
                    record.updated_at = db.func.current_timestamp()
                    db.session.commit()
                
                return result.get('data')
            else:
                current_app.logger.error(f"更新简道云记录失败: {result}")
                return None
        except Exception as e:
            current_app.logger.error(f"更新简道云记录异常: {str(e)}")
            return None
    
    def verify_webhook_signature(self, request_data, signature):
        """验证简道云Webhook签名"""
        if not signature or not self.webhook_secret:
            return False
        
        try:
            # 使用HMAC-SHA256算法验证签名
            hmac_obj = hmac.new(self.webhook_secret.encode('utf-8'), request_data.encode('utf-8'), hashlib.sha256)
            expected_signature = hmac_obj.hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            current_app.logger.error(f"验证Webhook签名异常: {str(e)}")
            return False
    
    def process_webhook_event(self, event_data):
        """处理Webhook事件"""
        try:
            # 局部导入以避免循环依赖
            from .business_processor import business_processor
            
            event_type = event_data.get('type')
            form_id = event_data.get('app', {}).get('id')
            record_data = event_data.get('data')
            record_id = record_data.get('_id') if record_data else None
            
            current_app.logger.info(f"接收到Webhook事件: 类型={event_type}, 表单ID={form_id}, 记录ID={record_id}")
            
            if event_type == 'data_add':
                # 处理新增记录事件
                existing_record = JDYRecord.query.filter_by(record_id=record_id).first()
                if not existing_record:
                    new_record = JDYRecord(
                        form_id=form_id,
                        record_id=record_id,
                        data=record_data
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    
                    # 调用业务处理器处理表单记录
                    success, message = business_processor.process_form_record(form_id, record_id, record_data)
                    if success:
                        return True, f"新增记录处理成功，{message}"
                    else:
                        return True, f"新增记录保存成功，但处理失败: {message}"
                else:
                    return False, "记录已存在"
                
            elif event_type == 'data_update':
                # 处理更新记录事件
                record = JDYRecord.query.filter_by(record_id=record_id).first()
                if record:
                    record.data = record_data
                    record.updated_at = db.func.current_timestamp()
                    db.session.commit()
                    return True, "更新记录处理成功"
                else:
                    return False, "记录不存在"
                
            elif event_type == 'data_delete':
                # 处理删除记录事件
                record = JDYRecord.query.filter_by(record_id=record_id).first()
                if record:
                    db.session.delete(record)
                    db.session.commit()
                    return True, "删除记录处理成功"
                else:
                    return False, "记录不存在"
            
            elif event_type == 'workflow_complete':
                # 处理流程完成事件
                flow_id = event_data.get('workflow', {}).get('id')
                success, message = business_processor.process_flow_complete(flow_id, form_id, record_id, record_data)
                if success:
                    return True, f"流程完成处理成功: {message}"
                else:
                    return False, message
                
            return False, f"不支持的事件类型: {event_type}"
        except Exception as e:
            current_app.logger.error(f"处理Webhook事件异常: {str(e)}")
            return False, str(e)