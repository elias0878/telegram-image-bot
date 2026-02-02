#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف الخادم لـ Render.com
إضافة نقطة فحص صحية للحفاظ على تشغيل البوت
"""

import os
import bot
from aiohttp import web
import asyncio

async def health_check(request):
    """فحص حالة الخادم"""
    return web.json_response({
        "status": "healthy",
        "bot": "running",
        "images_count": bot.get_images_count()
    })

async def start_bot():
    """تشغيل البوت في خلفية"""
    # تهيئة قاعدة البيانات
    bot.init_database()
    
    # إنشاء التطبيق
    application = bot.Application.builder().token(bot.BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(bot.CommandHandler("start", bot.start))
    application.add_handler(bot.CommandHandler("help", bot.help_command))
    application.add_handler(bot.CommandHandler("random", bot.random_command))
    application.add_handler(bot.CommandHandler("categories", bot.categories_command))
    application.add_handler(bot.CommandHandler("count", bot.count_command))
    application.add_handler(bot.CallbackQueryHandler(bot.button_click))
    
    # بدء البوت
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    return application

async def main():
    """الدالة الرئيسية"""
    port = int(os.environ.get('PORT', 10000))
    
    # إنشاء تطبيق الويب
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    # تشغيل البوت في خلفية
    bot_app = await start_bot()
    
    # تشغيل خادم الويب
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"✓ الخادم يعمل على المنفذ {port}")
    print("✓ البوت يعمل بنجاح!")
    
    # البقاء يعمل
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
