import os
import json
import requests
from datetime import datetime, timedelta
from .models import db, ExternalApiLog

class WeChatService:
    def __init__(self):
        # 从环境变量获取企业微信配置
        self.corpid = os.environ.get('WECHAT_CORPID', '')
        self.corpsecret = os.environ.get('WECHAT_CORPSECRET', '')
        self.agentid = os.environ.get('WECHAT_AGENTID', '')
        self.base_url = os.environ.get('WECHAT_API_URL', 'https://qyapi.weixin.qq.com/cgi-bin')
        
        # 用于缓存access_token
        self.access_token = None
        self.token_expire_time = datetime.now()
    
    def _get_access_token(self):
        """获取企业微信访问令牌"""
        # 检查token是否已过期
        if self.access_token and self.token_expire_time > datetime.now():
            return self.access_token
        
        # 构建请求URL
        url = f"{self.base_url}/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
        
        try:
            # 记录API调用日志
            start_time = datetime.now()
            response = requests.get(url)
            end_time = datetime.now()
            
            # 解析响应
            result = response.json()
            
            # 记录API调用结果
            self._log_api_call(
                url=url,
                method='GET',
                request_data={},
                response_data=result,
                status_code=response.status_code,
                execution_time=(end_time - start_time).total_seconds()
            )
            
            if result.get('errcode') == 0:
                # 更新缓存的token和过期时间（默认7200秒有效期，提前10分钟刷新）
                self.access_token = result.get('access_token')
                self.token_expire_time = datetime.now() + timedelta(seconds=7100)
                return self.access_token
            else:
                print(f"获取企业微信access_token失败: {result}")
                return None
        except Exception as e:
            print(f"获取企业微信access_token异常: {str(e)}")
            # 记录异常日志
            self._log_api_call(
                url=url,
                method='GET',
                request_data={},
                response_data={'error': str(e)},
                status_code=500,
                execution_time=0
            )
            return None
    
    def send_text_message(self, user_ids, content, safe=0):
        """
        发送文本消息给企业微信用户
        :param user_ids: 用户ID列表，用|分隔，如 "user1|user2|user3"
        :param content: 消息内容
        :param safe: 表示是否是保密消息，0表示否，1表示是，默认0
        :return: 发送结果
        """
        access_token = self._get_access_token()
        if not access_token:
            return {'errcode': -1, 'errmsg': '获取access_token失败'}
        
        # 构建请求URL
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        # 构建消息体
        message_data = {
            "touser": user_ids,
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": content
            },
            "safe": safe
        }
        
        try:
            # 记录API调用日志
            start_time = datetime.now()
            response = requests.post(url, json=message_data)
            end_time = datetime.now()
            
            # 解析响应
            result = response.json()
            
            # 记录API调用结果
            self._log_api_call(
                url=url,
                method='POST',
                request_data=message_data,
                response_data=result,
                status_code=response.status_code,
                execution_time=(end_time - start_time).total_seconds()
            )
            
            return result
        except Exception as e:
            print(f"发送企业微信消息异常: {str(e)}")
            # 记录异常日志
            self._log_api_call(
                url=url,
                method='POST',
                request_data=message_data,
                response_data={'error': str(e)},
                status_code=500,
                execution_time=0
            )
            return {'errcode': -1, 'errmsg': str(e)}
    
    def send_text_card_message(self, user_ids, title, description, url, btn_text="详情"):
        """
        发送文本卡片消息给企业微信用户
        :param user_ids: 用户ID列表，用|分隔
        :param title: 标题
        :param description: 描述，支持HTML标签
        :param url: 点击后跳转的链接
        :param btn_text: 按钮文字，默认为"详情"
        :return: 发送结果
        """
        access_token = self._get_access_token()
        if not access_token:
            return {'errcode': -1, 'errmsg': '获取access_token失败'}
        
        # 构建请求URL
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        # 构建消息体
        message_data = {
            "touser": user_ids,
            "msgtype": "textcard",
            "agentid": self.agentid,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btn_text
            }
        }
        
        try:
            # 记录API调用日志
            start_time = datetime.now()
            response = requests.post(url, json=message_data)
            end_time = datetime.now()
            
            # 解析响应
            result = response.json()
            
            # 记录API调用结果
            self._log_api_call(
                url=url,
                method='POST',
                request_data=message_data,
                response_data=result,
                status_code=response.status_code,
                execution_time=(end_time - start_time).total_seconds()
            )
            
            return result
        except Exception as e:
            print(f"发送企业微信文本卡片消息异常: {str(e)}")
            # 记录异常日志
            self._log_api_call(
                url=url,
                method='POST',
                request_data=message_data,
                response_data={'error': str(e)},
                status_code=500,
                execution_time=0
            )
            return {'errcode': -1, 'errmsg': str(e)}
    
    def _log_api_call(self, url, method, request_data, response_data, status_code, execution_time):
        """记录API调用日志到数据库"""
        try:
            # 提取URL中的access_token并隐藏
            masked_url = url
            if 'access_token=' in url:
                parts = url.split('access_token=')
                masked_url = parts[0] + 'access_token=***'
            
            # 创建日志记录
            log = ExternalApiLog(
                api_name='企业微信API',
                endpoint=masked_url,
                method=method,
                request_data=json.dumps(request_data) if isinstance(request_data, dict) else str(request_data),
                response_data=json.dumps(response_data) if isinstance(response_data, dict) else str(response_data),
                status_code=status_code,
                execution_time=execution_time
            )
            
            # 添加到数据库并提交
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"记录企业微信API调用日志失败: {str(e)}")
            # 发生异常时回滚
            try:
                db.session.rollback()
            except:
                pass

# 创建全局实例
wechat_service = WeChatService()