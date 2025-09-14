from flask import Blueprint, jsonify, request
from .jandoyun_service import JandoyunService
from .external_api_service import ExternalApiService
from .wechat_service import wechat_service
from .models import JandoyunRecord, ProcessingTask, db
from . import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/hello', methods=['GET'])
def hello():
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})

@api_bp.route('/jandoyun/webhook', methods=['POST'])
def jandoyun_webhook():
    """接收简道云Webhook事件"""
    try:
        # 获取请求数据
        data = request.json
        
        # 验证签名
        signature = request.headers.get('X-JDY-Signature')
        jandoyun_service = JandoyunService()
        
        # 注意：在实际验证时，需要使用原始请求体
        # 这里为了简化，直接使用JSON解析后的数据
        # 实际应用中应该使用request.get_data()获取原始数据
        is_valid = jandoyun_service.verify_webhook_signature(
            request_data=request.get_data(as_text=True),
            signature=signature
        )
        
        if not is_valid:
            return jsonify({'error': '签名验证失败'}), 401
        
        # 处理事件
        success, message = jandoyun_service.process_webhook_event(data)
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/jandoyun/records', methods=['POST'])
def create_jandoyun_record():
    """创建简道云表单记录"""
    try:
        data = request.json
        form_id = data.get('form_id')
        record_data = data.get('data')
        
        if not form_id or not record_data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        jandoyun_service = JandoyunService()
        result = jandoyun_service.create_record(form_id, record_data)
        
        if result:
            return jsonify({'success': True, 'data': result}), 201
        else:
            return jsonify({'success': False, 'error': '创建记录失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/jandoyun/records/<record_id>', methods=['PUT'])
def update_jandoyun_record(record_id):
    """更新简道云表单记录"""
    try:
        data = request.json
        form_id = data.get('form_id')
        record_data = data.get('data')
        
        if not form_id or not record_data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        jandoyun_service = JandoyunService()
        result = jandoyun_service.update_record(form_id, record_id, record_data)
        
        if result:
            return jsonify({'success': True, 'data': result}), 200
        else:
            return jsonify({'success': False, 'error': '更新记录失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/external-api/call', methods=['POST'])
def call_external_api():
    """调用外部API"""
    try:
        data = request.json
        endpoint = data.get('endpoint')
        method = data.get('method', 'GET')
        api_data = data.get('data')
        params = data.get('params')
        
        if not endpoint:
            return jsonify({'error': '缺少必要参数'}), 400
        
        external_api_service = ExternalApiService()
        result = external_api_service.call_api(
            endpoint=endpoint,
            method=method,
            data=api_data,
            params=params
        )
        
        if result is not None:
            return jsonify({'success': True, 'data': result}), 200
        else:
            return jsonify({'success': False, 'error': '调用外部API失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取处理任务列表"""
    try:
        status = request.args.get('status')
        task_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        query = ProcessingTask.query
        
        if status:
            query = query.filter_by(status=status)
        
        if task_type:
            query = query.filter_by(task_type=task_type)
        
        # 分页
        pagination = query.order_by(ProcessingTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tasks = []
        for task in pagination.items:
            tasks.append({
                'id': task.id,
                'type': task.task_type,
                'status': task.status,
                'priority': task.priority,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'error_message': task.error_message
            })
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/wechat/send-text', methods=['POST'])
def send_wechat_text_message():
    """发送企业微信文本消息"""
    try:
        data = request.json
        user_ids = data.get('user_ids')
        content = data.get('content')
        safe = data.get('safe', 0)
        
        if not user_ids or not content:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 发送消息
        result = wechat_service.send_text_message(user_ids, content, safe)
        
        if result.get('errcode') == 0:
            return jsonify({'success': True, 'message': '消息发送成功'}), 200
        else:
            return jsonify({'success': False, 'error': result.get('errmsg', '发送失败')}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/wechat/send-text-card', methods=['POST'])
def send_wechat_text_card_message():
    """发送企业微信文本卡片消息"""
    try:
        data = request.json
        user_ids = data.get('user_ids')
        title = data.get('title')
        description = data.get('description')
        url = data.get('url')
        btn_text = data.get('btn_text', '详情')
        
        if not user_ids or not title or not description or not url:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 发送消息
        result = wechat_service.send_text_card_message(user_ids, title, description, url, btn_text)
        
        if result.get('errcode') == 0:
            return jsonify({'success': True, 'message': '消息发送成功'}), 200
        else:
            return jsonify({'success': False, 'error': result.get('errmsg', '发送失败')}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/records', methods=['GET'])
def get_records():
    """获取简道云记录列表"""
    try:
        processed = request.args.get('processed')
        form_id = request.args.get('form_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        query = JandoyunRecord.query
        
        if processed is not None:
            query = query.filter_by(processed=processed.lower() == 'true')
        
        if form_id:
            query = query.filter_by(form_id=form_id)
        
        # 分页
        pagination = query.order_by(JandoyunRecord.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        records = []
        for record in pagination.items:
            records.append({
                'id': record.id,
                'form_id': record.form_id,
                'record_id': record.record_id,
                'data': record.data,
                'processed': record.processed,
                'process_result': record.process_result,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'records': records,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
