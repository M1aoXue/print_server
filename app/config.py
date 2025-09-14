import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 简道云配置
    JANDOYUN_APP_ID = os.getenv("JANDOYUN_APP_ID", "your_app_id")
    JANDOYUN_APP_SECRET = os.getenv("JANDOYUN_APP_SECRET", "your_app_secret")
    JANDOYUN_API_URL = os.getenv("JANDOYUN_API_URL", "https://api.jiandaoyun.com/v1/")
    JANDOYUN_WEBHOOK_SECRET = os.getenv("JANDOYUN_WEBHOOK_SECRET", "your_webhook_secret")
    
    # 外部API配置
    EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "https://api.example.com/")
    EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY", "your_external_api_key")
    
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
