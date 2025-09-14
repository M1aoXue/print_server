#!/bin/bash

# 生产环境启动脚本

# 确保脚本在出错时退出
set -e

# 打印使用说明
function show_help() {
    echo "生产环境启动脚本 - 使用Gunicorn运行Flask应用"
    echo ""
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  install   安装依赖包"
    echo "  start     启动生产服务器"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 install  # 安装所有依赖"
    echo "  $0 start    # 启动生产服务器"
}

# 安装依赖
function install_dependencies() {
    echo "正在安装依赖包..."
    pip install -r requirements.txt
    echo "依赖安装完成!"
}

# 启动生产服务器
function start_server() {
    echo "正在启动生产服务器..."
    
    # 检查是否设置了环境变量
    if [ -z "$SECRET_KEY" ]; then
        echo "警告: 未设置SECRET_KEY环境变量，使用默认值"
    fi
    
    if [ -z "$DATABASE_URI" ]; then
        echo "警告: 未设置DATABASE_URI环境变量，使用默认值"
    fi
    
    # 使用gunicorn启动应用
    # -w 4: 使用4个工作进程
    # -b 0.0.0.0:5001: 绑定到所有网络接口的5001端口
    # wsgi:app: 指向wsgi.py中的app对象
    gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
}

# 根据参数执行相应功能
case "$1" in
    install)
        install_dependencies
        ;;
    start)
        start_server
        ;;
    help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac