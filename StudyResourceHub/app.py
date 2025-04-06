import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize app
app = Flask(__name__)

# Configure database - use PostgreSQL in production or SQLite in development
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
# Fix for postgres:// issue in some cloud platforms
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.secret_key = os.environ.get("SESSION_SECRET", "your_fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Add a context processor to make the current date available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى لوحة التحكم'

# Import routes after initializing app and db to avoid circular imports
from models import Admin
from admin import admin_routes
from admin_tools import admin_tools_routes
import utils

# Register blueprints
app.register_blueprint(admin_routes)
app.register_blueprint(admin_tools_routes)

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Home route
@app.route('/')
def index():
    from flask import render_template
    from models import Subject
    subjects = Subject.query.all()
    return render_template('index.html', subjects=subjects)

# Subject route
@app.route('/subject/<int:subject_id>')
def subject(subject_id):
    from flask import render_template, abort
    from models import Subject, Section
    subject = Subject.query.get_or_404(subject_id)
    sections = Section.query.filter_by(subject_id=subject_id).all()
    return render_template('subject.html', subject=subject, sections=sections)

# Section route
@app.route('/section/<int:section_id>')
def section(section_id):
    from flask import render_template, abort
    from models import Section, File
    section = Section.query.get_or_404(section_id)
    files = File.query.filter_by(section_id=section_id).all()
    return render_template('section.html', section=section, files=files)

# Download file route
@app.route('/download/<int:file_id>')
def download_file(file_id):
    from flask import send_from_directory, abort
    from models import File, Section, Subject
    from werkzeug.utils import secure_filename
    
    file_record = File.query.get_or_404(file_id)
    
    # Increment download count
    file_record.download_count += 1
    db.session.commit()
    
    # Get the file's base directory from its relative path
    file_directory = os.path.dirname(file_record.file_path)
    file_basename = os.path.basename(file_record.file_path)
    
    # Full path to the directory containing the file
    full_directory_path = os.path.join(app.config['UPLOAD_FOLDER'], file_directory)
    full_file_path = os.path.join(full_directory_path, file_basename)
    
    # If the file doesn't exist at the expected path, try to find it in alternate locations
    if not os.path.exists(full_file_path):
        app.logger.debug(f"File not found at expected path: {full_file_path}")
        
        # Get section and subject info
        section = Section.query.get(file_record.section_id)
        subject = Subject.query.get(section.subject_id)
        
        # Try legacy path format: uploads/[subject_id]/[section_id]/filename
        legacy_dir = os.path.join(
            app.config['UPLOAD_FOLDER'],
            str(subject.id),
            str(section.id)
        )
        legacy_path = os.path.join(legacy_dir, file_record.filename)
        
        # Try new path format: uploads/[subject_id]_[subject_name]/[section_id]_[section_name]/filename
        subject_folder = f"{subject.id}_{secure_filename(subject.name)}"
        section_folder = f"{section.id}_{secure_filename(section.name)}"
        new_dir = os.path.join(
            app.config['UPLOAD_FOLDER'],
            subject_folder,
            section_folder
        )
        new_path = os.path.join(new_dir, file_record.filename)
        
        app.logger.debug(f"Trying legacy path: {legacy_path}")
        app.logger.debug(f"Trying new path: {new_path}")
        
        # Check which path exists and use it
        if os.path.exists(legacy_path):
            app.logger.info(f"Found file at legacy path: {legacy_path}")
            full_directory_path = legacy_dir
            
            # Update the file path in the database
            file_record.file_path = os.path.join(str(subject.id), str(section.id), file_record.filename)
            db.session.commit()
            
        elif os.path.exists(new_path):
            app.logger.info(f"Found file at new path: {new_path}")
            full_directory_path = new_dir
            
            # Update the file path in the database
            file_record.file_path = os.path.join(subject_folder, section_folder, file_record.filename)
            db.session.commit()
            
        else:
            app.logger.error(f"File not found in any location: {file_record.filename}")
            abort(404)  # File not found
    
    return send_from_directory(full_directory_path, file_basename, as_attachment=True, 
                              download_name=file_record.original_filename)

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create default admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Default admin account created.")
