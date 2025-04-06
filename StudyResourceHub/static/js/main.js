// ملف JavaScript الرئيسي للمنصة التعليمية

// التعامل مع شريط البحث الرئيسي
document.addEventListener('DOMContentLoaded', function() {
    // البحث المركزي في الصفحة الرئيسية
    initializeMainSearch();
    
    // تفعيل زر البحث
    const searchButton = document.querySelector('.search-section .btn-primary');
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const searchInput = document.getElementById('mainSearch');
            if (searchInput) {
                performSearch(searchInput.value);
            }
        });
    }
    
    // التعامل مع ضغط مفتاح Enter في مربع البحث
    const mainSearchInput = document.getElementById('mainSearch');
    if (mainSearchInput) {
        mainSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
    }
    
    // معالجة التمرير السلس للروابط
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                e.preventDefault();
                document.querySelector(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // معالجة التحقق من نموذج الملفات
    const uploadForm = document.getElementById('fileUploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('file');
            if (fileInput && fileInput.files.length === 0) {
                e.preventDefault();
                alert('الرجاء اختيار ملف للرفع');
            }
        });
    }
    
    // عرض اسم الملف المحدد عند اختياره
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileNameDisplay = document.getElementById('selectedFileName');
            if (fileNameDisplay) {
                if (this.files.length > 0) {
                    fileNameDisplay.textContent = this.files[0].name;
                    fileNameDisplay.parentElement.classList.remove('d-none');
                } else {
                    fileNameDisplay.parentElement.classList.add('d-none');
                }
            }
        });
    }
    
    // تطبيق معالج التمرير للصور في واجهة العرض
    handleSwipableCarousels();
});

// وظيفة البحث الرئيسية
function initializeMainSearch() {
    const mainSearchInput = document.getElementById('mainSearch');
    const subjectItems = document.querySelectorAll('.subject-item');
    const fileItems = document.querySelectorAll('.file-item');
    
    if (mainSearchInput) {
        mainSearchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            
            // البحث في المواد الدراسية
            if (subjectItems.length > 0) {
                subjectItems.forEach(subject => {
                    const title = subject.querySelector('.card-title').textContent.toLowerCase();
                    const description = subject.querySelector('.card-text') ? 
                                        subject.querySelector('.card-text').textContent.toLowerCase() : '';
                    
                    if (title.includes(searchTerm) || description.includes(searchTerm)) {
                        subject.style.display = 'block';
                    } else {
                        subject.style.display = 'none';
                    }
                });
            }
            
            // البحث في الملفات إذا كانت موجودة
            if (fileItems.length > 0) {
                fileItems.forEach(file => {
                    const fileName = file.querySelector('.file-name').textContent.toLowerCase();
                    const fileType = file.querySelector('.file-type') ? 
                                     file.querySelector('.file-type').textContent.toLowerCase() : '';
                    
                    if (fileName.includes(searchTerm) || fileType.includes(searchTerm)) {
                        file.style.display = 'block';
                    } else {
                        file.style.display = 'none';
                    }
                });
            }
        });
    }
}

// وظيفة إجراء البحث
function performSearch(query) {
    if (!query) return;
    
    query = query.toLowerCase().trim();
    
    // البحث في المواد والملفات المعروضة حاليًا
    const subjectItems = document.querySelectorAll('.subject-item');
    const fileItems = document.querySelectorAll('.file-item');
    let found = false;
    
    // البحث في المواد
    if (subjectItems.length > 0) {
        subjectItems.forEach(subject => {
            const title = subject.querySelector('.card-title').textContent.toLowerCase();
            const description = subject.querySelector('.card-text') ? 
                                subject.querySelector('.card-text').textContent.toLowerCase() : '';
            
            if (title.includes(query) || description.includes(query)) {
                subject.style.display = 'block';
                found = true;
                // تمييز العناصر المطابقة
                highlightElement(subject);
            } else {
                subject.style.display = 'none';
            }
        });
    }
    
    // البحث في الملفات
    if (fileItems.length > 0) {
        fileItems.forEach(file => {
            const fileName = file.querySelector('.file-name').textContent.toLowerCase();
            const fileType = file.querySelector('.file-type') ? 
                             file.querySelector('.file-type').textContent.toLowerCase() : '';
            
            if (fileName.includes(query) || fileType.includes(query)) {
                file.style.display = 'block';
                found = true;
                // تمييز العناصر المطابقة
                highlightElement(file);
            } else {
                file.style.display = 'none';
            }
        });
    }
    
    // عرض رسالة إذا لم يتم العثور على نتائج
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer) {
        if (!found) {
            resultsContainer.innerHTML = '<div class="alert alert-info">لم يتم العثور على نتائج مطابقة لـ "' + query + '"</div>';
        } else {
            resultsContainer.innerHTML = '';
        }
    }
}

// وظيفة لتمييز العناصر المطابقة
function highlightElement(element) {
    // إضافة فئة التمييز
    element.classList.add('search-highlight');
    
    // إزالة التمييز بعد فترة
    setTimeout(() => {
        element.classList.remove('search-highlight');
    }, 2000);
}

// التعامل مع التمرير للصور
function handleSwipableCarousels() {
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(carousel => {
        let startX, moved;
        const threshold = 100; // مقدار التمرير المطلوب للتبديل

        carousel.addEventListener('touchstart', e => {
            startX = e.touches[0].clientX;
            moved = false;
        }, { passive: true });

        carousel.addEventListener('touchmove', e => {
            if (!startX) return;
            const currentX = e.touches[0].clientX;
            const diff = startX - currentX;
            if (Math.abs(diff) > 10) moved = true;
        }, { passive: true });

        carousel.addEventListener('touchend', e => {
            if (!moved) return;
            const endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            
            if (Math.abs(diff) >= threshold) {
                const carouselInstance = bootstrap.Carousel.getInstance(carousel);
                if (diff > 0) {
                    carouselInstance.next();
                } else {
                    carouselInstance.prev();
                }
            }
            
            startX = null;
            moved = false;
        }, { passive: true });
    });
}
