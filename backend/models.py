import uuid
import json
from datetime import datetime
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ProductUpdate(db.Model):
    __tablename__ = 'product_updates'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product = db.Column(db.String(100), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False) # blog, changelog, github, social
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    update_type = db.Column(db.String(50), nullable=True, index=True) # feature, bug, ai, pricing, strategy
    tags = db.Column(db.Text, nullable=True)  # Store as JSON string for SQLite compatibility
    engagement = db.Column(db.Integer, default=0)
    publish_time = db.Column(db.DateTime, nullable=False, index=True)
    source_url = db.Column(db.String(1000), unique=True, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False, index=True) # For de-duplication
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.Text, nullable=True)  # Store as JSON string for SQLite compatibility

    # Composite indexes for performance optimization
    __table_args__ = (
        Index('idx_product_publish_time', 'product', 'publish_time'),
        Index('idx_update_type_publish_time', 'update_type', 'publish_time'),
    )
    
    @property
    def tags_list(self):
        """Get tags as a list"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    @tags_list.setter
    def tags_list(self, value):
        """Set tags from a list"""
        if value:
            self.tags = json.dumps(value)
        else:
            self.tags = None
    
    @property
    def raw_data_dict(self):
        """Get raw_data as a dict"""
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except:
                return {}
        return {}
    
    @raw_data_dict.setter
    def raw_data_dict(self, value):
        """Set raw_data from a dict"""
        if value:
            self.raw_data = json.dumps(value)
        else:
            self.raw_data = None

    def to_dict(self):
        return {
            "id": str(self.id),
            "product": self.product,
            "source_type": self.source_type,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "update_type": self.update_type,
            "tags": self.tags_list,
            "engagement": self.engagement,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CompetitiveLandscape(db.Model):
    __tablename__ = 'competitors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    github_repo = db.Column(db.String(255))
    rss_url = db.Column(db.String(255))
    changelog_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)


class DataSourceHealth(db.Model):
    """数据源健康状态监控"""
    __tablename__ = 'data_source_health'
    
    id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False)  # rss, github, social, changelog
    last_success_time = db.Column(db.DateTime, nullable=True)
    last_failure_time = db.Column(db.DateTime, nullable=True)
    consecutive_failures = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='unknown')  # healthy, warning, error, unknown
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "status": self.status,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TaskExecutionLog(db.Model):
    """任务执行日志"""
    __tablename__ = 'task_execution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False, index=True)
    task_type = db.Column(db.String(50), nullable=False)  # collection, analysis, report
    status = db.Column(db.String(20), nullable=False)  # success, failure, running
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    task_metadata = db.Column(db.Text, nullable=True)  # Store as JSON string for SQLite compatibility
    
    @property
    def metadata_dict(self):
        """Get metadata as a dict"""
        if self.task_metadata:
            try:
                return json.loads(self.task_metadata)
            except:
                return {}
        return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value):
        """Set metadata from a dict"""
        if value:
            self.task_metadata = json.dumps(value)
        else:
            self.task_metadata = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "metadata": self.metadata_dict
        }
