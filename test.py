import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入应用模块
from app import create_app, db
from app.models import JandoyunRecord, ExternalApiLog, ProcessingTask
from app.jandoyun_service import JandoyunService
from app.external_api_service import ExternalApiService

# 创建测试应用实例
app = create_app('development')

# 测试函数
with app.app_context():
    print("===== 开始测试简道云对接系统 =====")
    
    # 1. 测试数据库连接
    print("\n1. 测试数据库连接...")
    try:
        # 创建测试表（如果不存在）
        db.create_all()
        print("✅ 数据库连接成功！")
        
        # 2. 测试添加测试数据
        print("\n2. 测试添加测试数据...")
        try:
            # 添加测试记录
            test_record = JandoyunRecord(
                form_id="test_form_id",
                record_id=f"test_record_{datetime.now().timestamp()}",
                data={"name": "测试记录", "status": "测试中"}
            )
            db.session.add(test_record)
            
            # 添加测试任务
            test_task = ProcessingTask(
                task_type="test_task",
                data={"test_key": "test_value"}
            )
            db.session.add(test_task)
            
            # 添加测试日志
            test_log = ExternalApiLog(
                endpoint="/test",
                method="GET",
                status_code=200,
                success=True
            )
            db.session.add(test_log)
            
            db.session.commit()
            print(f"✅ 添加测试数据成功！添加了 {test_record}, {test_task}, {test_log}")
            
            # 3. 测试查询数据
            print("\n3. 测试查询数据...")
            try:
                # 查询最近添加的记录
                recent_records = JandoyunRecord.query.order_by(JandoyunRecord.created_at.desc()).limit(1).all()
                recent_tasks = ProcessingTask.query.order_by(ProcessingTask.created_at.desc()).limit(1).all()
                recent_logs = ExternalApiLog.query.order_by(ExternalApiLog.created_at.desc()).limit(1).all()
                
                print(f"✅ 查询数据成功！\n- 记录数量: {len(recent_records)}\n- 任务数量: {len(recent_tasks)}\n- 日志数量: {len(recent_logs)}")
                
            except Exception as e:
                print(f"❌ 查询数据失败: {str(e)}")
                
        except Exception as e:
            print(f"❌ 添加测试数据失败: {str(e)}")
            db.session.rollback()
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("提示：请检查.env文件中的数据库配置是否正确。")
        
    # 4. 测试服务初始化
    print("\n4. 测试服务初始化...")
    try:
        jandoyun_service = JandoyunService()
        external_api_service = ExternalApiService()
        print("✅ 服务初始化成功！")
        
        # 显示配置信息（不显示敏感信息）
        print("\n5. 配置信息摘要:")
        print(f"- 简道云API URL: {app.config['JANDOYUN_API_URL']}")
        print(f"- 外部API URL: {app.config['EXTERNAL_API_URL']}")
        print(f"- 数据库URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@***")
        
    except Exception as e:
        print(f"❌ 服务初始化失败: {str(e)}")
        print("提示：请检查.env文件中的配置是否完整。")
        
    print("\n===== 测试完成 =====")
    
    print("\n下一步操作建议：")
    print("1. 确保.env文件中的所有配置项都已正确填写")
    print("2. 运行 'python run.py' 启动应用服务器")
    print("3. 在简道云中配置Webhook，指向 http://your-server:5001/api/jandoyun/webhook")
    print("4. 使用API测试工具（如Postman）测试各个API端点")