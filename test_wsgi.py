#!/usr/bin/env python3

"""
测试WSGI入口点的简单脚本

此脚本用于验证wsgi.py文件是否能正确加载应用
"""

import os
import sys
from werkzeug.serving import run_simple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_wsgi():
    """测试WSGI入口点"""
    try:
        # 导入WSGI应用
        from wsgi import app
        
        print("✅ 成功导入WSGI应用")
        print(f"📦 应用配置名称: {app.config.get('ENV')}")
        print(f"🔧 调试模式: {app.config.get('DEBUG')}")
        print(f"🗄️  数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        # 列出所有注册的路由
        print("\n📋 注册的路由:")
        for rule in app.url_map.iter_rules():
            print(f"   {rule}")
        
        print("\n🎉 WSGI入口点测试成功！")
        print("\n💡 提示：在生产环境中，请使用以下命令运行：")
        print("   ./start_production.sh start")
        print("   或")
        print("   gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app")
        
    except Exception as e:
        print(f"❌ WSGI入口点测试失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    test_wsgi()