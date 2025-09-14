import time
import json
import hmac
import hashlib
import requests
from flask import current_app
from .models import JandoyunRecord, db

class JandoyunService:
    def __init__(self):
        self.app_id = current_app.config['JANDOYUN_APP_ID']
        self.app_secret = current_app.config['JANDOYUN_APP_SECRET']
        self.api_url = current_app.config['JANDOYUN_API_URL']
        self.webhook_secret = current_app.config['JANDOYUN_WEBHOOK_SECRET']
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
                new_record = JandoyunRecord(
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
                record = JandoyunRecord.query.filter_by(record_id=record_id).first()
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
        """处理简道云Webhook事件"""
        try:
            # 获取事件类型和数据
            event_type = event_data.get('type')
            form_id = event_data.get('app', {}).get('id')
            record_data = event_data.get('data')
            record_id = record_data.get('_id') if record_data else None
            
            if event_type == 'data_add':
                # 处理新增记录事件
                existing_record = JandoyunRecord.query.filter_by(record_id=record_id).first()
                if not existing_record:
                    new_record = JandoyunRecord(
                        form_id=form_id,
                        record_id=record_id,
                        data=record_data
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    return True, "新增记录处理成功"
                
            elif event_type == 'data_update':
                # 处理更新记录事件
                record = JandoyunRecord.query.filter_by(record_id=record_id).first()
                if record:
                    record.data = record_data
                    record.updated_at = db.func.current_timestamp()
                    db.session.commit()
                    return True, "更新记录处理成功"
            
            elif event_type == 'data_delete':
                # 处理删除记录事件
                record = JandoyunRecord.query.filter_by(record_id=record_id).first()
                if record:
                    db.session.delete(record)
                    db.session.commit()
                    return True, "删除记录处理成功"
            
            return False, "不支持的事件类型或记录不存在"
        except Exception as e:
            current_app.logger.error(f"处理Webhook事件异常: {str(e)}")
            return False, str(e)