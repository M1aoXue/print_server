from flask import current_app
import json

class ConfigManager:
    """配置管理器，用于管理表单ID、流程ID等配置"""
    
    def __init__(self):
        self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        # 需要监听的表单配置
        self.form_configs = {
            # 示例表单配置，可以根据实际情况修改
            "data_form": {
                "id": current_app.config.get('DATA_FORM_ID', ''),
                "name": "数据表单",
                "process_required": True  # 是否需要进行复杂处理
            },
            "process_form": {
                "id": current_app.config.get('PROCESS_FORM_ID', ''),
                "name": "流程表单",
                "process_required": False
            }
        }
        
        # 需要监听的流程配置
        self.flow_configs = {
            "main_flow": {
                "id": current_app.config.get('MAIN_FLOW_ID', ''),
                "name": "主流程"
            }
        }
        
        # 计算任务相关配置
        self.calculation_task_config = {
            "endpoint": current_app.config.get('CALCULATION_TASK_ENDPOINT', 'tasks/calculate'),
            "poll_endpoint": current_app.config.get('CALCULATION_RESULT_ENDPOINT', 'tasks/result'),
            "poll_interval": current_app.config.get('CALCULATION_POLL_INTERVAL', 60),  # 轮询间隔（秒）
            "max_retries": current_app.config.get('CALCULATION_MAX_RETRIES', 30)  # 最大重试次数
        }
        
        # 企业微信通知配置
        self.wechat_notify_config = {
            "enabled": current_app.config.get('WECHAT_NOTIFY_ENABLED', True),
            "default_receivers": current_app.config.get('WECHAT_DEFAULT_RECEIVERS', '').split(','),
            "notify_level": current_app.config.get('WECHAT_NOTIFY_LEVEL', 'info')  # info, warning, error
        }
    
    def get_form_config(self, form_key):
        """获取指定表单的配置"""
        return self.form_configs.get(form_key, {})
    
    def get_flow_config(self, flow_key):
        """获取指定流程的配置"""
        return self.flow_configs.get(flow_key, {})
    
    def get_calculation_config(self):
        """获取计算任务配置"""
        return self.calculation_task_config
    
    def get_wechat_config(self):
        """获取企业微信通知配置"""
        return self.wechat_notify_config
    
    def is_form_process_required(self, form_id):
        """检查指定表单是否需要处理"""
        for config in self.form_configs.values():
            if config.get('id') == form_id:
                return config.get('process_required', False)
        return False
    
    def is_flow_monitored(self, flow_id):
        """检查指定流程是否需要监控"""
        for config in self.flow_configs.values():
            if config.get('id') == flow_id:
                return True
        return False

# 创建配置管理器实例
config_manager = ConfigManager()