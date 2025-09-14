import time
import requests
from flask import current_app
from .models import ExternalApiLog, db

class ExternalApiService:
    def __init__(self):
        self.api_url = current_app.config['EXTERNAL_API_URL']
        self.api_key = current_app.config['EXTERNAL_API_KEY']
    
    def _prepare_headers(self):
        """准备请求头"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        return headers
    
    def _log_api_call(self, endpoint, method, request_data, response_data, status_code, duration, success):
        """记录API调用日志"""
        try:
            log_entry = ExternalApiLog(
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response_data,
                status_code=status_code,
                duration=duration,
                success=success
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"记录API调用日志失败: {str(e)}")
    
    def call_api(self, endpoint, method='GET', data=None, params=None):
        """调用外部API的通用方法"""
        full_url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._prepare_headers()
        start_time = time.time()
        
        try:
            response = None
            if method.upper() == 'GET':
                response = requests.get(full_url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(full_url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(full_url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(full_url, headers=headers, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 计算请求耗时
            duration = time.time() - start_time
            
            # 尝试解析响应数据
            response_data = None
            if response.content:
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = response.text
            
            # 记录日志
            success = 200 <= response.status_code < 300
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                request_data=data if method in ['POST', 'PUT'] else params,
                response_data=response_data,
                status_code=response.status_code,
                duration=duration,
                success=success
            )
            
            response.raise_for_status()  # 如果状态码不是2xx，抛出异常
            
            return response_data
        except requests.exceptions.RequestException as e:
            # 请求异常处理
            duration = time.time() - start_time
            status_code = response.status_code if response else 0
            
            # 记录失败日志
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                request_data=data if method in ['POST', 'PUT'] else params,
                response_data=str(e),
                status_code=status_code,
                duration=duration,
                success=False
            )
            
            current_app.logger.error(f"调用外部API失败 ({full_url}): {str(e)}")
            return None
        except Exception as e:
            # 其他异常处理
            duration = time.time() - start_time
            
            # 记录失败日志
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                request_data=data if method in ['POST', 'PUT'] else params,
                response_data=str(e),
                status_code=0,
                duration=duration,
                success=False
            )
            
            current_app.logger.error(f"调用外部API发生未知错误 ({full_url}): {str(e)}")
            return None