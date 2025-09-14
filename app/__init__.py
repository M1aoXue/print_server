from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()

# 加载环境变量
load_dotenv()

def create_app(config_name='development'):
    app = Flask(__name__)

    # 加载配置
    if config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from .routes import main
    app.register_blueprint(main)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 初始化调度器
    from .scheduler import scheduler_manager
    with app.app_context():
        scheduler_manager.init_app(app)

    # 导入模型以确保被SQLAlchemy识别
    with app.app_context():
        from . import models

    return app
