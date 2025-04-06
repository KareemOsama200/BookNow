from app import db
from flask_login import UserMixin
from datetime import datetime

class Admin(UserMixin, db.Model):
    """Admin user model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Subject(db.Model):
    """Subject model to store academic subjects like math, physics, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with sections
    sections = db.relationship('Section', backref='subject', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Subject {self.name}>'

class Section(db.Model):
    """Section model to store categories within subjects like explanations, tests, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with files
    files = db.relationship('File', backref='section', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Section {self.name} (Subject: {self.subject_id})>'

class File(db.Model):
    """File model to store uploaded educational materials"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    download_count = db.Column(db.Integer, default=0)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<File {self.original_filename} (Section: {self.section_id})>'
