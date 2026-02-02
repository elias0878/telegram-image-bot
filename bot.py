#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام لعرض صور عشوائية من قاعدة البيانات
"""

import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'images.db')
IMAGES_FOLDER = os.environ.get('IMAGES_FOLDER', 'images')

# إنشاء المجلدات إذا لم تكن موجودة
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def init_database():
    """إنشاء قاعدة البيانات والجداول"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            file_unique_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✓ تم إنشاء قاعدة البيانات بنجاح")

def add_image_to_db(filename, category='general'):
    """إضافة صورة لقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO images (filename, category) VALUES (?, ?)',
            (filename, category)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"⚠ الصورة {filename} موجودة مسبقاً")
        conn.close()
        return False

def get_random_image(category=None):
    """الحصول على صورة عشوائية من قاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if category and category != 'all':
        cursor.execute(
            'SELECT id, filename, category FROM images WHERE category = ? ORDER BY RANDOM() LIMIT 1',
            (category,)
        )
    else:
        cursor.execute('SELECT id, filename, category FROM images ORDER BY RANDOM() LIMIT 1')
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'id': result[0], 'filename': result[1], 'category': result[2]}
    return None

def get_all_categories():
    """الحصول على جميع التصنيفات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM images WHERE category IS NOT NULL GROUP BY category')
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories if categories else ['general']

def get_images_count():
    """الحصول على عدد الصور في قاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM images')
    count = cursor.fetchone()[0]
    conn.close()
    return count

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /start"""
    user_name = update.message.from_user.first_name
    images_count = get_images_count()
    
    welcome_message = f"""
🎉 **مرحباً يا {user_name}!**

أنا بوت الصور العشوائية 📸

• عدد الصور المتاحة: {images_count}
• اضغط على الزر أدناه للحصول على صورة عشوائية

✨ استمتع!
    """
    
    keyboard = [
        [InlineKeyboardButton("🎲 احصل على صورة عشوائية", callback_data="random_image")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /help"""
    help_text = """
🆘 **مساعدة**

**الأوامر المتاحة:**
• /start - بدء البوت
• /help - عرض المساعدة
• /random - الحصول على صورة عشوائية
• /categories - عرض التصنيفات
• /count - عرض عدد الصور

**الاستخدام:**
اضغط على زر "🎲 صورة عشوائية" وسيتم إرسال صورة عشوائية من قاعدة البيانات!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /random"""
    image_data = get_random_image()
    
    if not image_data:
        await update.message.reply_text("⚠️ لا توجد صور في قاعدة البيانات حالياً!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🎲 صورة عشوائية أخرى", callback_data="random_image")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # إرسال الصورة
    image_path = os.path.join(IMAGES_FOLDER, image_data['filename'])
    if os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"📸 {image_data['filename']}\nالتصنيف: {image_data['category']}",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            f"📸 {image_data['filename']}\nالتصنيف: {image_data['category']}\n\n(الملف غير موجود)",
            reply_markup=reply_markup
        )

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /categories"""
    categories = get_all_categories()
    
    if not categories:
        await update.message.reply_text("⚠️ لا توجد تصنيفات حالياً!")
        return
    
    categories_text = "**التصنيفات المتاحة:**\n\n" + "\n".join([f"• {cat}" for cat in categories])
    
    keyboard = [
        [InlineKeyboardButton("🎲 عشوائي", callback_data="random_image")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(categories_text, reply_markup=reply_markup, parse_mode='Markdown')

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /count"""
    count = get_images_count()
    await update.message.reply_text(f"📊 عدد الصور في قاعدة البيانات: {count}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "random_image":
        image_data = get_random_image()
        
        if not image_data:
            await query.edit_message_text("⚠️ لا توجد صور في قاعدة البيانات حالياً!")
            return
        
        keyboard = [
            [InlineKeyboardButton("🎲 صورة عشوائية أخرى", callback_data="random_image")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال الصورة
        image_path = os.path.join(IMAGES_FOLDER, image_data['filename'])
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=f"📸 {image_data['filename']}\nالتصنيف: {image_data['category']}",
                    reply_markup=reply_markup
                )
            await query.message.delete()
        else:
            await query.edit_message_text(
                text=f"📸 {image_data['filename']}\nالتصنيف: {image_data['category']}\n\n(الملف غير موجود)",
                reply_markup=reply_markup
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    if update:
        await update.message.reply_text("⚠️ حدث خطأ، يرجى المحاولة مرة أخرى!")

def main():
    """الدالة الرئيسية"""
    logger.info("🤖 جاري تشغيل البوت...")
    
    # التحقق من وجود التوكن
    if not BOT_TOKEN:
        logger.error("❌ لم يتم تعيين BOT_TOKEN!")
        return
    
    # تهيئة قاعدة البيانات
    init_database()
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("random", random_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("count", count_command))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # معالجة الأخطاء
    application.add_error_handler(error_handler)
    
    # تشغيل البوت
    logger.info("✓ البوت يعمل!")
    application.run_polling()

if __name__ == "__main__":
    main()
