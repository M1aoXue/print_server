# 简道云对接系统

这是一个基于Flask的系统，用于与简道云平台对接，实现Webhook监听、表单记录管理、外部API交互和定时任务调度等功能。

## 功能特性

- **简道云Webhook监听**：接收并验证简道云发送的Webhook事件
- **简道云表单管理**：创建和更新简道云表单记录
- **外部REST API交互**：与第三方API进行数据交互
- **定时任务调度**：定期执行轮询和数据处理任务
- **MySQL数据库集成**：使用SQLAlchemy ORM进行数据库操作

## 技术栈

- **后端框架**：Flask 2.3.3
- **数据库ORM**：SQLAlchemy 2.0.20
- **数据库**：MySQL 8.0+
- **定时任务**：APScheduler 3.10.1
- **HTTP客户端**：Requests 2.31.0
- **环境配置**：python-dotenv 1.0.0

## 安装指南

### 1. 克隆项目

```bash
# 克隆项目代码
```

### 2. 创建虚拟环境

```bash
cd print_server
python3 -m venv venv
```

### 3. 激活虚拟环境

**MacOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

复制.env.example文件并重命名为.env，然后根据实际情况修改配置：

```bash
cp .env.example .env
# 编辑.env文件，填写实际的配置值
```

### 6. 初始化数据库

```bash
flask db init
flask db migrate
flask db upgrade
```

### 7. 运行应用

**开发环境:**
```bash
python run.py
```

应用将在 http://localhost:5001 启动

**注意：** `python run.py` 仅适用于开发环境，在生产环境中应使用下面介绍的生产级WSGI服务器。

### 8. 生产环境部署

本项目提供了使用Gunicorn（生产级WSGI服务器）运行的配置。

#### 8.1 安装生产依赖

```bash
./start_production.sh install
```

或者手动安装：

```bash
pip install gunicorn
```

#### 8.2 启动生产服务器

使用提供的启动脚本：

```bash
./start_production.sh start
```

或者直接使用gunicorn命令：

```bash
gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

其中参数说明：
- `-w 4`：使用4个工作进程（可根据服务器CPU核心数调整）
- `-b 0.0.0.0:5001`：绑定到所有网络接口的5001端口
- `wsgi:app`：指向wsgi.py文件中的app对象

#### 8.3 生产环境配置注意事项

1. **环境变量配置**：确保在生产环境中正确设置所有必要的环境变量，特别是：
   - `SECRET_KEY`：设置为强随机值，用于会话安全
   - `DATABASE_URI`：生产环境的数据库连接字符串
   - 各种API密钥和密码

2. **关闭调试模式**：生产环境配置已默认关闭调试模式（DEBUG=False）

3. **使用HTTPS**：在生产环境中，建议通过反向代理（如Nginx）配置HTTPS

4. **日志管理**：生产环境中应配置适当的日志级别和日志轮转

## API端点

### 简道云相关

- **POST /api/jdy/webhook**：接收简道云Webhook事件
- **POST /api/jdy/records**：创建简道云表单记录
- **PUT /api/jdy/records/<record_id>**：更新简道云表单记录

### 外部API相关

- **POST /api/external-api/call**：调用外部API

### 数据查询相关

- **GET /api/records**：获取简道云记录列表
- **GET /api/tasks**：获取处理任务列表

### 企业微信相关

- **POST /api/wechat/send-text**：发送企业微信文本消息
- **POST /api/wechat/send-text-card**：发送企业微信文本卡片消息

## 配置说明

### 数据库配置

- **DATABASE_URI**：MySQL数据库连接字符串，格式为 `mysql+mysqlconnector://username:password@localhost:3306/database_name`

### 简道云配置

- **JDY_APP_ID**：简道云应用ID
- **JDY_APP_SECRET**：简道云应用密钥
- **JDY_API_URL**：简道云API基础URL
- **JDY_WEBHOOK_SECRET**：简道云Webhook密钥，用于验证签名

### 外部API配置

- **EXTERNAL_API_URL**：外部API基础URL
- **EXTERNAL_API_KEY**：外部API访问密钥

### 企业微信配置

- **WECHAT_CORPID**：企业ID
- **WECHAT_CORPSECRET**：应用的凭证密钥
- **WECHAT_AGENTID**：应用ID
- **WECHAT_API_URL**：企业微信API基础URL（默认为https://qyapi.weixin.qq.com/cgi-bin）

## 定时任务

系统包含以下定时任务：

1. **每5分钟**：检查并处理未处理的简道云记录
2. **每10分钟**：轮询外部API获取最新数据
3. **每天凌晨2点**：清理一周前的API调用日志

## 部署说明

### 生产环境配置

在生产环境中，建议：

1. 使用Gunicorn或uWSGI作为WSGI服务器
2. 使用Nginx作为反向代理
3. 配置SSL证书以启用HTTPS
4. 关闭DEBUG模式
5. 设置强密码和密钥

### Docker部署（可选）

可以创建Dockerfile和docker-compose.yml文件进行容器化部署。

## 开发说明

### 项目结构

```
print_server/
├── app/
│   ├── __init__.py       # 应用初始化
│   ├── api.py            # API路由定义
│   ├── config.py         # 配置文件
│   ├── routes.py         # 网页路由
│   ├── models.py         # 数据库模型
│   ├── jdy_service.py # 简道云服务
│   ├── external_api_service.py # 外部API服务
│   ├── scheduler.py      # 定时任务调度器
│   ├── static/           # 静态文件
│   └── templates/        # 模板文件
├── instance/             # 实例配置
├── .env.example          # 环境变量示例
├── requirements.txt      # 依赖列表
└── run.py                # 启动脚本
```

### 开发流程

1. 创建新功能分支
2. 实现功能并编写代码
3. 运行测试确保功能正常
4. 提交代码并创建Pull Request

## 注意事项

1. 确保.env文件中的敏感信息（如密钥、密码）不被提交到代码仓库
2. 定期备份数据库
3. 监控系统日志，及时发现和解决问题
4. 根据实际业务需求调整定时任务的执行频率