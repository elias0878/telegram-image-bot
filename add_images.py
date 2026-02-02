#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إضافة الصور لقاعدة البيانات
"""

import os
import sqlite3
import glob

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'images.db')
IMAGES_FOLDER = os.environ.get('IMAGES_FOLDER', 'images')

# أنواع الملفات المدعومة
SUPPORTED_FORMATS = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']

def init_database():
    """إنشاء قاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ تم إنشاء قاعدة البيانات")

def add_image(filename, category='general'):
    """إضافة صورة واحدة"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO images (filename, category) VALUES (?, ?)',
            (filename, category)
        )
        conn.commit()
        print(f"✓ تم إضافة: {filename}")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠ موجودة مسبقاً: {filename}")
        return False
    finally:
        conn.close()

def add_all_images_from_folder(category='general'):
    """إضافة جميع الصور من مجلد"""
    if not os.path.exists(IMAGES_FOLDER):
        print(f"❌ المجلد {IMAGES_FOLDER} غير موجود!")
        return
    
    init_database()
    
    total_added = 0
    total_skipped = 0
    
    for format_pattern in SUPPORTED_FORMATS:
        pattern = os.path.join(IMAGES_FOLDER, format_pattern)
        files = glob.glob(pattern)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            if add_image(filename, category):
                total_added += 1
            else:
                total_skipped += 1
    
    print(f"\n📊 النتيجة:")
    print(f"   ✓ تم إضافة: {total_added}")
    print(f"   ⚠ تم تخطي: {total_skipped}")
    print(f"   📁 المجلد: {IMAGES_FOLDER}")

def show_stats():
    """عرض إحصائيات قاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM images')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT category, COUNT(*) FROM images GROUP BY category')
    by_category = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 إحصائيات قاعدة البيانات:")
    print(f"   إجمالي الصور: {total}")
    print(f"\n   حسب التصنيف:")
    for cat, count in by_category:
        print(f"   • {cat}: {count}")

def list_images():
    """عرض جميع الصور"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, filename, category, created_at FROM images ORDER BY id')
    images = cursor.fetchall()
    
    conn.close()
    
    if not images:
        print("❌ لا توجد صور في قاعدة البيانات!")
        return
    
    print(f"\n📋 قائمة الصور ({len(images)}):")
    for img in images:
        print(f"   {img[0]}. {img[1]} ({img[2]}) - {img[3]}")

def delete_image(image_id):
    """حذف صورة"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
    conn.commit()
    affected = cursor.rowcount
    
    conn.close()
    
    if affected:
        print(f"✓ تم حذف الصورة رقم {image_id}")
    else:
        print(f"❌ لم يتم العثور على الصورة رقم {image_id}")

if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("   أداة إدارة صور بوت تيليجرام")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'add':
            category = sys.argv[2] if len(sys.argv) > 2 else 'general'
            add_all_images_from_folder(category)
        
        elif command == 'stats':
            show_stats()
        
        elif command == 'list':
            list_images()
        
        elif command == 'delete':
            if len(sys.argv) > 2:
                delete_image(sys.argv[2])
            else:
                print("❌ يرجى تحديد رقم الصورة!")
                print("   مثال: python add_images.py delete 1")
        
        else:
            print("❌ أمر غير معروف!")
            print("\nالأوامر المتاحة:")
            print("   python add_images.py add [category]  - إضافة جميع الصور")
            print("   python add_images.py stats           - عرض الإحصائيات")
            print("   python add_images.py list            - قائمة الصور")
            print("   python add_images.py delete [id]     - حذف صورة")
    else:
        show_stats()
        list_images()
