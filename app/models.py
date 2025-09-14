from datetime import datetime
from . import db

class JDYRecord(db.Model):
    __tablename__ = 'jdy_records'
    
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.String(50), nullable=False, unique=True)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    process_result = db.Column(db.String(255))

class ExternalApiLog(db.Model):
    __tablename__ = 'external_api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    request_data = db.Column(db.JSON)
    response_data = db.Column(db.JSON)
    status_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Float)
    success = db.Column(db.Boolean, default=False)

class ProcessingTask(db.Model):
    __tablename__ = 'processing_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    priority = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = db.Column(db.Text)