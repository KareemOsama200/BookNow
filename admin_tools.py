import os
import uuid
import re
from flask import Blueprint, current_app, render_template, request, flash, redirect, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db, Subject, Section, File

# إنشاء blueprint للأدوات الإدارية
admin_tools_routes = Blueprint('admin_tools', __name__, url_prefix='/admin/tools')

@admin_tools_routes.route('/')
@login_required
def tools_index():
    """الصفحة الرئيسية للأدوات الإدارية"""
    return render_template('admin/tools/index.html')

@admin_tools_routes.route('/sync-folders', methods=['GET', 'POST'])
@login_required
def sync_folders():
    """مزامنة الملفات المضافة يدويًا في المجلدات مع قاعدة البيانات"""
    
    # استخراج بنية المجلدات الحالية
    folder_structure = {}
    uploads_folder = current_app.config['UPLOAD_FOLDER']
    
    # Get all subjects and sections from database
    subjects = Subject.query.all()
    # Create dictionaries with both ID and name-based keys
    subjects_by_id = {str(subject.id): subject for subject in subjects}
    # Regular expression to match subject folder pattern: ID_NAME format
    subject_folder_pattern = re.compile(r'^(\d+)_(.+)$')
    
    # Dictionary to track subject ID from folder name
    subject_folder_to_id = {}
    
    # Collect all sections for quick lookup
    sections = Section.query.all()
    sections_by_id = {(str(section.subject_id), str(section.id)): section for section in sections}
    section_folder_pattern = re.compile(r'^(\d+)_(.+)$')
    
    # Dictionary to track section ID from folder name
    section_folder_to_id = {}
    
    # Scan the uploads folder
    for subject_folder in os.listdir(uploads_folder):
        # Skip hidden files
        if subject_folder.startswith('.'):
            continue
        
        subject_path = os.path.join(uploads_folder, subject_folder)
        if not os.path.isdir(subject_path):
            continue
            
        # Check if the folder matches our named pattern (ID_NAME)
        subject_match = subject_folder_pattern.match(subject_folder)
        subject_id = None
        subject_exists = False
        subject_name = "غير موجود"
        
        if subject_match:
            # Extract the ID part from the folder name
            subject_id = subject_match.group(1)
            subject_folder_to_id[subject_folder] = subject_id
            
            # Check if this subject exists in database
            if subject_id in subjects_by_id:
                subject_exists = True
                subject_name = subjects_by_id[subject_id].name
        else:
            # Try to find if this is a legacy folder with just ID
            if subject_folder.isdigit() and subject_folder in subjects_by_id:
                subject_id = subject_folder
                subject_exists = True
                subject_name = subjects_by_id[subject_id].name
        
        # If we couldn't match a subject ID, skip this folder
        if not subject_id:
            continue
            
        # Add this subject folder to our structure
        folder_structure[subject_folder] = {
            'id': subject_id,
            'name': subject_name,
            'exists': subject_exists,
            'sections': {}
        }
        
        # Scan for section folders
        for section_folder in os.listdir(subject_path):
            section_path = os.path.join(subject_path, section_folder)
            
            if not os.path.isdir(section_path):
                continue
                
            # Check if the folder matches our named pattern (ID_NAME)
            section_match = section_folder_pattern.match(section_folder)
            section_id = None
            section_exists = False
            section_name = "غير موجود"
            
            if section_match:
                # Extract the ID part from the folder name
                section_id = section_match.group(1)
                section_folder_to_id[subject_folder + '/' + section_folder] = section_id
                
                # Check if this section exists in database
                if (subject_id, section_id) in sections_by_id:
                    section_exists = True
                    section_name = sections_by_id[(subject_id, section_id)].name
            else:
                # Try to find if this is a legacy folder with just ID
                if section_folder.isdigit() and (subject_id, section_folder) in sections_by_id:
                    section_id = section_folder
                    section_exists = True
                    section_name = sections_by_id[(subject_id, section_id)].name
            
            # If we couldn't match a section ID, skip this folder
            if not section_id:
                continue
                
            # Collect files in this section
            files = []
            for file_item in os.listdir(section_path):
                file_path = os.path.join(section_path, file_item)
                if os.path.isfile(file_path) and not file_item.startswith('.'):
                    # Create the relative path matching our new folder structure
                    relative_path = os.path.join(subject_folder, section_folder, file_item)
                    
                    # Also check for legacy path format
                    legacy_path = os.path.join(subject_id, section_id, file_item)
                    
                    # Check if file exists in database with either path format
                    file_exists = File.query.filter(
                        (File.file_path == relative_path) | 
                        (File.file_path == legacy_path)
                    ).first() is not None
                    
                    files.append({
                        'name': file_item,
                        'exists': file_exists,
                        'path': relative_path,
                        'size': os.path.getsize(file_path)
                    })
            
            folder_structure[subject_folder]['sections'][section_folder] = {
                'id': section_id,
                'name': section_name,
                'exists': section_exists,
                'files': files
            }
    
    # Process form submission to add files to database
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_file':
            section_id = request.form.get('section_id')
            subject_id = request.form.get('subject_id')
            file_path = request.form.get('file_path')
            file_name = os.path.basename(file_path)
            
            # Get file type from extension
            file_extension = os.path.splitext(file_name)[1].lower()
            if file_extension in ['.pdf']:
                file_type = 'pdf'
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                file_type = 'image'
            elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                file_type = 'video'
            elif file_extension in ['.doc', '.docx']:
                file_type = 'doc'
            elif file_extension in ['.ppt', '.pptx']:
                file_type = 'ppt'
            elif file_extension in ['.xls', '.xlsx']:
                file_type = 'xls'
            else:
                file_type = 'other'
            
            # Create file record in database
            new_file = File(
                filename=file_name,
                original_filename=file_name,
                file_path=file_path,
                file_type=file_type,
                section_id=section_id
            )
            
            db.session.add(new_file)
            db.session.commit()
            flash(f'تمت إضافة الملف {file_name} بنجاح.', 'success')
            
            # Redirect to refresh the page and show updated data
            return redirect(url_for('admin_tools.sync_folders'))
    
    return render_template('admin/tools/sync_folders.html', folder_structure=folder_structure)


@admin_tools_routes.route('/folder-info')
@login_required
def folder_info():
    """عرض معلومات عن بنية المجلدات"""
    
    subjects = Subject.query.all()
    
    # إنشاء مسار المجلد لكل مادة وقسم
    folder_info = []
    
    for subject in subjects:
        # Use the new subject folder naming convention: ID_NAME
        subject_folder_name = f"{subject.id}_{secure_filename(subject.name)}"
        subject_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subject_folder_name)
        
        # Check both new and legacy (ID-only) folder formats
        legacy_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(subject.id))
        
        subject_exists = os.path.exists(subject_folder) or os.path.exists(legacy_folder)
        
        subject_data = {
            'id': subject.id,
            'name': subject.name,
            'folder_name': subject_folder_name,
            'folder_path': subject_folder,
            'legacy_path': legacy_folder,
            'folder_exists': subject_exists,
            'sections': []
        }
        
        for section in subject.sections:
            # Use the new section folder naming convention: ID_NAME
            section_folder_name = f"{section.id}_{secure_filename(section.name)}"
            
            # New folder path
            section_folder = os.path.join(subject_folder, section_folder_name)
            
            # Check both new and legacy formats
            legacy_section_folder = os.path.join(legacy_folder, str(section.id))
            
            section_exists = os.path.exists(section_folder) or os.path.exists(legacy_section_folder)
            
            section_data = {
                'id': section.id,
                'name': section.name,
                'folder_name': section_folder_name,
                'folder_path': section_folder,
                'legacy_path': legacy_section_folder,
                'folder_exists': section_exists
            }
            
            subject_data['sections'].append(section_data)
        
        folder_info.append(subject_data)
    
    return render_template('admin/tools/folder_info.html', folder_info=folder_info)


@admin_tools_routes.route('/clean-uploads', methods=['GET', 'POST'])
@login_required
def clean_uploads():
    """تنظيف مجلد الملفات من المجلدات والملفات غير المستخدمة"""
    
    folders_to_clean = []
    uploads_folder = current_app.config['UPLOAD_FOLDER']
    
    # Get all subjects and sections for reference
    subjects = Subject.query.all()
    subject_ids = [str(s.id) for s in subjects]
    
    # Get all subject folders (id_name format and legacy id format)
    subject_folders = {f"{s.id}_{secure_filename(s.name)}": s for s in subjects}
    
    # Create a regex pattern to match ID_name format folders
    subject_pattern = re.compile(r'^(\d+)_')
    
    # Scan uploads folder for any folders not matching our subjects
    for folder in os.listdir(uploads_folder):
        if folder.startswith('.'):
            continue
            
        folder_path = os.path.join(uploads_folder, folder)
        if not os.path.isdir(folder_path):
            continue
            
        # Check if this is a valid subject folder
        is_valid = False
        
        # Check if this is a new format folder (ID_NAME)
        subject_match = subject_pattern.match(folder)
        if subject_match:
            subject_id = subject_match.group(1)
            if subject_id in subject_ids:
                is_valid = True
        # Check if this is a legacy format folder (just ID)
        elif folder in subject_ids:
            is_valid = True
            
        if not is_valid:
            folders_to_clean.append({
                'path': folder_path,
                'name': folder,
                'type': 'subject',
                'contents': os.listdir(folder_path) if os.path.exists(folder_path) else []
            })
    
    # Handle POST request for cleaning
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'clean_folder':
            folder_path = request.form.get('folder_path')
            
            # Verify folder still exists and is in the uploads directory
            if os.path.exists(folder_path) and os.path.commonpath([folder_path, uploads_folder]) == uploads_folder:
                # Remove the folder and all contents
                for root, dirs, files in os.walk(folder_path, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                        
                os.rmdir(folder_path)
                flash(f'تم حذف المجلد {os.path.basename(folder_path)} بنجاح.', 'success')
            else:
                flash('لم يتم العثور على المجلد.', 'danger')
                
            return redirect(url_for('admin_tools.clean_uploads'))
            
    return render_template('admin/tools/clean_uploads.html', folders_to_clean=folders_to_clean)