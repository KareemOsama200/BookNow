import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db
from models import Admin, Subject, Section, File
import uuid

# Create blueprint
admin_routes = Blueprint('admin', __name__, url_prefix='/admin')

# Admin login route
@admin_routes.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
    
    return render_template('admin/login.html')

# Admin logout route
@admin_routes.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'success')
    return redirect(url_for('admin.admin_login'))

# Admin dashboard
@admin_routes.route('/dashboard')
@login_required
def dashboard():
    # Get counts for the dashboard
    subjects_count = Subject.query.count()
    sections_count = Section.query.count()
    files_count = File.query.count()
    total_downloads = db.session.query(db.func.sum(File.download_count)).scalar() or 0
    
    # Get top downloaded files
    top_files = File.query.order_by(File.download_count.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          subjects_count=subjects_count,
                          sections_count=sections_count,
                          files_count=files_count,
                          total_downloads=total_downloads,
                          top_files=top_files)

# Subjects management
@admin_routes.route('/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Add new subject
        if action == 'add':
            name = request.form.get('name')
            description = request.form.get('description', '')
            
            if not name:
                flash('يرجى إدخال اسم المادة.', 'danger')
            else:
                new_subject = Subject(name=name, description=description)
                db.session.add(new_subject)
                db.session.commit()
                
                # Create directory for this subject
                subject_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    str(new_subject.id)
                )
                os.makedirs(subject_path, exist_ok=True)
                
                flash('تمت إضافة المادة بنجاح.', 'success')
        
        # Edit subject
        elif action == 'edit':
            subject_id = request.form.get('subject_id')
            name = request.form.get('name')
            description = request.form.get('description', '')
            
            subject = Subject.query.get_or_404(subject_id)
            subject.name = name
            subject.description = description
            db.session.commit()
            flash('تم تحديث المادة بنجاح.', 'success')
        
        # Delete subject
        elif action == 'delete':
            subject_id = request.form.get('subject_id')
            subject = Subject.query.get_or_404(subject_id)
            
            # Get all sections for this subject
            sections = Section.query.filter_by(subject_id=subject_id).all()
            
            # For each section, delete files
            for section in sections:
                files = File.query.filter_by(section_id=section.id).all()
                for file in files:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting file: {e}")
            
            # Delete subject from database (cascades to sections and files)
            db.session.delete(subject)
            db.session.commit()
            
            flash('تم حذف المادة وجميع الأقسام والملفات المرتبطة بها.', 'success')
    
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

# Sections management
@admin_routes.route('/sections/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def manage_sections(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Add new section
        if action == 'add':
            name = request.form.get('name')
            description = request.form.get('description', '')
            
            if not name:
                flash('يرجى إدخال اسم القسم.', 'danger')
            else:
                new_section = Section(
                    name=name, 
                    description=description,
                    subject_id=subject_id
                )
                db.session.add(new_section)
                db.session.commit()
                
                # Create directory for this section
                section_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    str(subject_id),
                    str(new_section.id)
                )
                os.makedirs(section_path, exist_ok=True)
                
                flash('تمت إضافة القسم بنجاح.', 'success')
        
        # Edit section
        elif action == 'edit':
            section_id = request.form.get('section_id')
            name = request.form.get('name')
            description = request.form.get('description', '')
            
            section = Section.query.get_or_404(section_id)
            section.name = name
            section.description = description
            db.session.commit()
            flash('تم تحديث القسم بنجاح.', 'success')
        
        # Delete section
        elif action == 'delete':
            section_id = request.form.get('section_id')
            section = Section.query.get_or_404(section_id)
            
            # Get files in this section
            files_to_delete = File.query.filter_by(section_id=section_id).all()
            
            # Delete each file
            for file in files_to_delete:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file: {e}")
            
            # Delete section from database 
            db.session.delete(section)
            db.session.commit()
            
            flash('تم حذف القسم وجميع الملفات المرتبطة به.', 'success')
    
    sections = Section.query.filter_by(subject_id=subject_id).all()
    return render_template('admin/sections.html', subject=subject, sections=sections)

# Files management
@admin_routes.route('/files/<int:section_id>', methods=['GET', 'POST'])
@login_required
def manage_files(section_id):
    section = Section.query.get_or_404(section_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Add new file
        if action == 'add':
            if 'file' not in request.files:
                flash('لم يتم تحديد ملف.', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            
            if file.filename == '':
                flash('لم يتم تحديد ملف.', 'danger')
                return redirect(request.url)
            
            if file:
                # Generate a safe filename with UUID to avoid conflicts
                original_filename = secure_filename(file.filename)
                filename_parts = os.path.splitext(original_filename)
                unique_filename = f"{uuid.uuid4().hex}{filename_parts[1]}"
                
                # Get subject and section objects for folder naming
                subject = Subject.query.get(section.subject_id)
                
                # Create sanitized folder names using subject and section names
                subject_folder_name = f"{subject.id}_{secure_filename(subject.name)}"
                section_folder_name = f"{section.id}_{secure_filename(section.name)}"
                
                # Create directory structure with meaningful names
                section_dir = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    subject_folder_name,
                    section_folder_name
                )
                os.makedirs(section_dir, exist_ok=True)
                
                # Save the file to the section directory
                file_path = os.path.join(section_dir, unique_filename)
                file.save(file_path)
                
                # Get file type from form instead of extension
                file_type = request.form.get('file_type')
                
                # If no file type is specified, determine from extension
                if not file_type:
                    file_extension = os.path.splitext(original_filename)[1].lower()
                    if file_extension in ['.pdf']:
                        file_type = 'pdf'
                    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                        file_type = 'image'
                    elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                        file_type = 'video'
                    else:
                        file_type = 'other'
                
                # Create database record with path to file in section folder
                relative_path = os.path.join(
                    subject_folder_name,
                    section_folder_name,
                    unique_filename
                )
                
                new_file = File(
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_path=relative_path,
                    file_type=file_type,
                    section_id=section_id
                )
                db.session.add(new_file)
                db.session.commit()
                flash('تم رفع الملف بنجاح.', 'success')
                
        # Delete file
        elif action == 'delete':
            file_id = request.form.get('file_id')
            file = File.query.get_or_404(file_id)
            
            # Delete the file from the filesystem
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file: {e}")
            
            # Delete from database
            db.session.delete(file)
            db.session.commit()
            flash('تم حذف الملف بنجاح.', 'success')
    
    files = File.query.filter_by(section_id=section_id).all()
    return render_template('admin/files.html', section=section, files=files)

# Statistics page
@admin_routes.route('/stats')
@login_required
def stats():
    # Get total downloads
    total_downloads = db.session.query(db.func.sum(File.download_count)).scalar() or 0
    
    # Get all files ordered by download count
    files = File.query.order_by(File.download_count.desc()).all()
    
    # Get most popular subjects
    subject_downloads = db.session.query(
        Subject.name, 
        db.func.sum(File.download_count).label('downloads')
    ).join(Section, Subject.id == Section.subject_id)\
     .join(File, Section.id == File.section_id)\
     .group_by(Subject.name)\
     .order_by(db.func.sum(File.download_count).desc())\
     .limit(5).all()
    
    return render_template('admin/stats.html', 
                          total_downloads=total_downloads,
                          files=files,
                          subject_downloads=subject_downloads)

# Change admin password
@admin_routes.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if current password is correct
        if not check_password_hash(current_user.password_hash, current_password):
            flash('كلمة المرور الحالية غير صحيحة.', 'danger')
            return redirect(url_for('admin.change_password'))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة غير متطابقة.', 'danger')
            return redirect(url_for('admin.change_password'))
        
        # Check password length
        if len(new_password) < 6:
            flash('كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل.', 'danger')
            return redirect(url_for('admin.change_password'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('تم تغيير كلمة المرور بنجاح.', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/change_password.html')
