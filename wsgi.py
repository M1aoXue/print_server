from app import create_app

# 创建生产环境的应用实例
app = create_app('production')

if __name__ == '__main__':
    # 这个主函数主要是为了方便测试，实际生产环境应该使用Gunicorn等WSGI服务器运行
    app.run(host='0.0.0.0', port=5001)