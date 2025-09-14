import requests
import json
import time
from flask import current_app
import hashlib
import base64
import urllib.parse

class WechatNotificationService:
    def __init__(self):
        # 从配置中获取企业微信相关参数
        self.corpid = current_app.config.get('WECHAT_CORPID', '')
        self.agentid = current_app.config.get('WECHAT_AGENTID', '')
        self.corpsecret = current_app.config.get('WECHAT_CORPSECRET', '')
        self.api_base_url = 'https://qyapi.weixin.qq.com/cgi-bin'
        
        # 用于缓存access_token
        self._access_token = None
        self._token_expires_at = 0
    
    def _get_access_token(self):
        """获取企业微信access_token"""
        # 检查token是否有效
        current_time = time.time()
        if self._access_token and current_time < self._token_expires_at:
            return self._access_token
        
        # 重新获取token
        url = f'{self.api_base_url}/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}'
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('errcode') == 0:
                self._access_token = data.get('access_token')
                # token有效期为2小时，提前2分钟过期
                self._token_expires_at = current_time + (data.get('expires_in', 7200) - 120)
                current_app.logger.info("成功获取企业微信access_token")
                return self._access_token
            else:
                error_msg = f"获取企业微信access_token失败: {data.get('errmsg', '')}"
                current_app.logger.error(error_msg)
                return None
        except Exception as e:
            current_app.logger.error(f"获取企业微信access_token异常: {str(e)}")
            return None
    
    def send_text_message(self, content, touser='@all', toparty='', totag=''):
        """发送文本消息"""
        access_token = self._get_access_token()
        if not access_token:
            return False, "获取access_token失败"
        
        url = f'{self.api_base_url}/message/send?access_token={access_token}'
        
        # 构建消息体
        message = {
            "touser": touser,
            "toparty": toparty,
            "totag": totag,
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": content
            },
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0
        }
        
        return self._send_message(url, message)
    
    def send_textcard_message(self, title, description, url, btntxt='详情', touser='@all', toparty='', totag=''):
        """发送文本卡片消息"""
        access_token = self._get_access_token()
        if not access_token:
            return False, "获取access_token失败"
        
        url = f'{self.api_base_url}/message/send?access_token={access_token}'
        
        # 构建消息体
        message = {
            "touser": touser,
            "toparty": toparty,
            "totag": totag,
            "msgtype": "textcard",
            "agentid": self.agentid,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btntxt
            },
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0
        }
        
        return self._send_message(url, message)
    
    def send_news_message(self, articles, touser='@all', toparty='', totag=''):
        """发送图文消息"""
        access_token = self._get_access_token()
        if not access_token:
            return False, "获取access_token失败"
        
        url = f'{self.api_base_url}/message/send?access_token={access_token}'
        
        # 构建消息体
        message = {
            "touser": touser,
            "toparty": toparty,
            "totag": totag,
            "msgtype": "news",
            "agentid": self.agentid,
            "news": {
                "articles": articles
            },
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0
        }
        
        return self._send_message(url, message)
    
    def _send_message(self, url, message):
        """发送消息的通用方法"""
        try:
            response = requests.post(url, json=message, timeout=10)
            data = response.json()
            
            if data.get('errcode') == 0:
                current_app.logger.info(f"发送企业微信消息成功: {message.get('msgtype')}")
                return True, "发送成功"
            else:
                error_msg = f"发送企业微信消息失败: {data.get('errmsg', '')}"
                current_app.logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            current_app.logger.error(f"发送企业微信消息异常: {str(e)}")
            return False, str(e)
    
    def send_processing_status(self, record_id, status, details=''):
        """发送处理状态通知"""
        content = f"【处理状态通知】\n记录ID: {record_id}\n状态: {status}\n详情: {details}"
        return self.send_text_message(content)
    
    def send_workflow_complete(self, workflow_id, form_id, status, result=''):
        """发送流程完成通知"""
        content = f"【流程完成通知】\n流程ID: {workflow_id}\n表单ID: {form_id}\n状态: {status}\n结果: {result}"
        return self.send_text_message(content)
    
    def send_error_notification(self, error_type, message, details=''):
        """发送错误通知"""
        content = f"【错误通知】\n类型: {error_type}\n消息: {message}\n详情: {details}"
        # 可以配置错误通知发送给特定的管理员
        admin_users = current_app.config.get('WECHAT_ADMIN_USERS', '@all')
        return self.send_text_message(content, touser=admin_users)
    
    def send_task_completion(self, task_id, task_type, status, result=''):
        """发送任务完成通知"""
        content = f"【任务完成通知】\n任务ID: {task_id}\n任务类型: {task_type}\n状态: {status}\n结果: {result}"
        return self.send_text_message(content)