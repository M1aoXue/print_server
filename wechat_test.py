#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信消息发送测试工具

这个脚本用于测试企业微信消息发送功能，提供了两种方式：
1. 直接调用wechat_service模块发送消息
2. 通过API接口发送消息

使用前请确保已在.env文件中配置了企业微信相关环境变量：
- WECHAT_CORPID
- WECHAT_CORPSECRET
- WECHAT_AGENTID

使用方法：
1. 直接运行脚本：python wechat_test.py
2. 根据提示输入相关参数
"""

import os
import json
import requests
import time
from dotenv import load_dotenv
from app.wechat_service import wechat_service

# 加载环境变量
def load_environment():
    """加载环境变量配置"""
    load_dotenv()
    
    # 检查必要的企业微信配置是否存在
    required_vars = ['WECHAT_CORPID', 'WECHAT_CORPSECRET', 'WECHAT_AGENTID']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"警告：以下企业微信环境变量未设置：{', '.join(missing_vars)}")
        print("请在.env文件中配置这些变量后重试")
        return False
    
    return True

# 方法1：直接调用wechat_service发送消息
def test_direct_message():
    """直接调用wechat_service模块发送消息"""
    print("\n=== 直接调用企业微信服务测试 ===")
    
    # 获取用户输入
    user_ids = input("请输入接收消息的用户ID（多个用户用|分隔）：")
    message_type = input("请选择消息类型（text/text_card）：").strip().lower()
    
    if message_type == 'text':
        content = input("请输入消息内容：")
        safe = input("是否为保密消息？(0/1，默认0)：")
        safe = int(safe) if safe else 0
        
        print(f"\n正在发送文本消息给用户：{user_ids}")
        result = wechat_service.send_text_message(user_ids, content, safe)
        
    elif message_type == 'text_card':
        title = input("请输入卡片标题：")
        description = input("请输入卡片描述（支持HTML标签）：")
        url = input("请输入点击跳转的URL：")
        btn_text = input("请输入按钮文字（默认'详情'）：") or "详情"
        
        print(f"\n正在发送文本卡片消息给用户：{user_ids}")
        result = wechat_service.send_text_card_message(
            user_ids, title, description, url, btn_text
        )
    else:
        print("不支持的消息类型，仅支持text和text_card")
        return False
    
    # 显示结果
    print(f"发送结果：{result}")
    if result.get('errcode') == 0:
        print("✅ 消息发送成功！")
        return True
    else:
        print(f"❌ 消息发送失败：{result.get('errmsg', '未知错误')}")
        return False

# 方法2：通过API接口发送消息
def test_api_message():
    """通过API接口发送消息"""
    print("\n=== API接口调用测试 ===")
    
    # 获取用户输入
    base_url = input("请输入API基础URL（默认http://localhost:5001）：") or "http://localhost:5001"
    user_ids = input("请输入接收消息的用户ID（多个用户用|分隔）：")
    message_type = input("请选择消息类型（text/text_card）：").strip().lower()
    
    headers = {'Content-Type': 'application/json'}
    
    if message_type == 'text':
        content = input("请输入消息内容：")
        safe = input("是否为保密消息？(0/1，默认0)：")
        safe = int(safe) if safe else 0
        
        url = f"{base_url}/api/wechat/send-text"
        data = {
            'user_ids': user_ids,
            'content': content,
            'safe': safe
        }
        
    elif message_type == 'text_card':
        title = input("请输入卡片标题：")
        description = input("请输入卡片描述（支持HTML标签）：")
        url = f"{base_url}/api/wechat/send-text-card"
        click_url = input("请输入点击跳转的URL：")
        btn_text = input("请输入按钮文字（默认'详情'）：") or "详情"
        
        data = {
            'user_ids': user_ids,
            'title': title,
            'description': description,
            'url': click_url,
            'btn_text': btn_text
        }
    else:
        print("不支持的消息类型，仅支持text和text_card")
        return False
    
    print(f"\n正在通过API发送{message_type}消息到{url}")
    print(f"请求数据：{data}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        # 显示结果
        print(f"HTTP状态码：{response.status_code}")
        print(f"API响应：{result}")
        
        if response.status_code == 200 and result.get('success'):
            print("✅ API调用成功，消息已发送！")
            return True
        else:
            error_msg = result.get('error', '未知错误')
            print(f"❌ API调用失败：{error_msg}")
            return False
    except Exception as e:
        print(f"❌ 发送请求时发生异常：{str(e)}")
        print("请确认API服务是否已启动")
        return False

# 打印配置信息摘要
def print_config_summary():
    """打印当前配置信息摘要"""
    print("\n=== 当前企业微信配置信息摘要 ===")
    print(f"企业ID: {os.environ.get('WECHAT_CORPID', '未设置')}")
    print(f"应用ID: {os.environ.get('WECHAT_AGENTID', '未设置')}")
    print(f"企业微信API URL: {os.environ.get('WECHAT_API_URL', '未设置')}")
    print("================================")

# 主函数
def main():
    """主函数"""
    print("===== 企业微信消息发送测试工具 =====")
    
    # 加载环境变量
    if not load_environment():
        return
    
    # 打印配置摘要
    print_config_summary()
    
    # 询问测试方式
    test_method = input("\n请选择测试方式：\n1. 直接调用wechat_service\n2. 通过API接口调用\n请输入1或2：")
    
    if test_method == '1':
        test_direct_message()
    elif test_method == '2':
        test_api_message()
    else:
        print("无效的选择，请输入1或2")
    
    print("\n测试完成！")

if __name__ == '__main__':
    main()