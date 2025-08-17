#!/usr/bin/env python3
"""
Telegram бот для сбора обратной связи от пользователей
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        ConversationHandler, filters, ContextTypes
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Telegram библиотеки не установлены. Установите: pip install python-telegram-bot")

# Импорты для работы с БД
try:
    from backend.app.models.feedback import Feedback, FeedbackType, FeedbackStatus
    from backend.app.core.database import SessionLocal
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️ Backend модули недоступны, используем локальное хранение")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOOSING_TYPE, ENTERING_SUBJECT, ENTERING_MESSAGE, ENTERING_CONTACT = range(4)

class TelegramFeedbackBot:
    """Telegram бот для сбора обратной связи"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.user_sessions = {}  # Для хранения данных пользователей
        
        # Инициализация бота
        if TELEGRAM_AVAILABLE:
            self.application = Application.builder().token(token).build()
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        
        # Обработчик команды /start
        start_handler = CommandHandler("start", self.start_command)
        self.application.add_handler(start_handler)
        
        # Обработчик команды /feedback
        feedback_handler = CommandHandler("feedback", self.feedback_command)
        self.application.add_handler(feedback_handler)
        
        # Обработчик команды /help
        help_handler = CommandHandler("help", self.help_command)
        self.application.add_handler(help_handler)
        
        # Conversation handler для сбора обратной связи
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("send_feedback", self.start_feedback)],
            states={
                CHOOSING_TYPE: [CallbackQueryHandler(self.choose_feedback_type)],
                ENTERING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_subject)],
                ENTERING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_message)],
                ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_contact)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_feedback)]
        )
        self.application.add_handler(conv_handler)
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        
        welcome_text = """
🤖 **Добро пожаловать в Crypto Analytics Platform!**

Я помогу вам получить информацию о криптовалютных сигналах и аналитике.

**Доступные команды:**
📊 `/feedback` - Отправить обратную связь
❓ `/help` - Получить помощь
📈 `/signals` - Последние сигналы
📰 `/news` - Новости рынка

**Есть вопросы или предложения?** 
Используйте команду `/feedback` для связи с нами!
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /feedback"""
        
        feedback_text = """
📝 **Обратная связь**

Спасибо, что хотите связаться с нами! 

**Как отправить обратную связь:**
1. Используйте команду `/send_feedback`
2. Выберите тип обратной связи
3. Укажите тему
4. Напишите ваше сообщение
5. При желании оставьте контакт для ответа

**Типы обратной связи:**
❓ **Вопрос** - Задать вопрос о продукте
💡 **Предложение** - Предложить улучшения
🐛 **Ошибка** - Сообщить о проблеме
🚀 **Функция** - Запросить новую функцию
📝 **Общее** - Любое другое сообщение

Нажмите `/send_feedback` чтобы начать!
        """
        
        await update.message.reply_text(feedback_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        
        help_text = """
❓ **Справка по командам**

**Основные команды:**
📊 `/feedback` - Информация об обратной связи
📈 `/signals` - Последние торговые сигналы
📰 `/news` - Новости криптовалютного рынка
📊 `/stats` - Статистика платформы

**Обратная связь:**
📝 `/send_feedback` - Отправить обратную связь
❌ `/cancel` - Отменить отправку обратной связи

**Дополнительно:**
🔗 `/website` - Ссылка на веб-сайт
📧 `/contact` - Контактная информация

**Нужна помощь?** Используйте `/feedback` для связи с поддержкой!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def start_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса отправки обратной связи"""
        
        # Создаем сессию для пользователя
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {
            'user_id': user_id,
            'username': update.effective_user.username,
            'first_name': update.effective_user.first_name,
            'last_name': update.effective_user.last_name
        }
        
        # Создаем клавиатуру с типами обратной связи
        keyboard = [
            [
                InlineKeyboardButton("❓ Вопрос", callback_data="question"),
                InlineKeyboardButton("💡 Предложение", callback_data="suggestion")
            ],
            [
                InlineKeyboardButton("🐛 Ошибка", callback_data="bug_report"),
                InlineKeyboardButton("🚀 Функция", callback_data="feature_request")
            ],
            [
                InlineKeyboardButton("📝 Общее", callback_data="general")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 **Выберите тип обратной связи:**\n\n"
            "❓ **Вопрос** - Задать вопрос о продукте\n"
            "💡 **Предложение** - Предложить улучшения\n"
            "🐛 **Ошибка** - Сообщить о проблеме\n"
            "🚀 **Функция** - Запросить новую функцию\n"
            "📝 **Общее** - Любое другое сообщение",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return CHOOSING_TYPE
    
    async def choose_feedback_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора типа обратной связи"""
        
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        feedback_type = query.data
        
        # Сохраняем тип обратной связи
        self.user_sessions[user_id]['feedback_type'] = feedback_type
        
        await query.edit_message_text(
            "📝 **Введите тему вашего сообщения:**\n\n"
            "Например: 'Проблема с отображением сигналов' или 'Предложение по улучшению интерфейса'",
            parse_mode='Markdown'
        )
        
        return ENTERING_SUBJECT
    
    async def enter_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода темы"""
        
        user_id = update.effective_user.id
        subject = update.message.text
        
        # Сохраняем тему
        self.user_sessions[user_id]['subject'] = subject
        
        await update.message.reply_text(
            "📝 **Введите ваше сообщение:**\n\n"
            "Опишите подробно ваш вопрос, предложение или проблему. "
            "Чем больше деталей, тем лучше мы сможем вам помочь!",
            parse_mode='Markdown'
        )
        
        return ENTERING_MESSAGE
    
    async def enter_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода сообщения"""
        
        user_id = update.effective_user.id
        message = update.message.text
        
        # Сохраняем сообщение
        self.user_sessions[user_id]['message'] = message
        
        await update.message.reply_text(
            "📧 **Хотите оставить контакт для ответа?**\n\n"
            "Вы можете указать:\n"
            "• Email адрес\n"
            "• Telegram username\n"
            "• Или просто написать 'нет' если не хотите оставлять контакт\n\n"
            "Мы ответим вам в течение 24 часов!",
            parse_mode='Markdown'
        )
        
        return ENTERING_CONTACT
    
    async def enter_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода контакта"""
        
        user_id = update.effective_user.id
        contact = update.message.text
        
        # Получаем данные сессии
        session_data = self.user_sessions.get(user_id, {})
        
        # Определяем тип контакта
        user_email = None
        user_telegram = None
        
        if contact.lower() in ['нет', 'no', 'n']:
            pass
        elif '@' in contact and '.' in contact:
            user_email = contact
        elif contact.startswith('@'):
            user_telegram = contact
        else:
            user_telegram = f"@{contact}" if not contact.startswith('@') else contact
        
        # Сохраняем обратную связь
        success = await self.save_feedback(
            user_id=user_id,
            username=session_data.get('username'),
            feedback_type=session_data.get('feedback_type'),
            subject=session_data.get('subject'),
            message=session_data.get('message'),
            user_email=user_email,
            user_telegram=user_telegram
        )
        
        if success:
            await update.message.reply_text(
                "✅ **Спасибо за вашу обратную связь!**\n\n"
                "📝 **Ваше сообщение:**\n"
                f"**Тип:** {self.get_feedback_type_name(session_data.get('feedback_type'))}\n"
                f"**Тема:** {session_data.get('subject')}\n"
                f"**Сообщение:** {session_data.get('message')[:100]}...\n\n"
                "Мы рассмотрим ваше сообщение и ответим в ближайшее время!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ **Произошла ошибка при сохранении обратной связи.**\n\n"
                "Пожалуйста, попробуйте позже или свяжитесь с нами другим способом.",
                parse_mode='Markdown'
            )
        
        # Очищаем сессию
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        return ConversationHandler.END
    
    async def cancel_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена отправки обратной связи"""
        
        user_id = update.effective_user.id
        
        # Очищаем сессию
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await update.message.reply_text(
            "❌ **Отправка обратной связи отменена.**\n\n"
            "Если у вас есть вопросы, используйте команду `/feedback` в любое время!",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def save_feedback(self, user_id: int, username: str, feedback_type: str, 
                          subject: str, message: str, user_email: str = None, 
                          user_telegram: str = None) -> bool:
        """Сохранение обратной связи в БД"""
        
        try:
            if DB_AVAILABLE:
                db = SessionLocal()
                try:
                    # Создаем объект обратной связи
                    feedback = Feedback(
                        user_id=user_id,
                        user_email=user_email,
                        user_telegram=user_telegram,
                        feedback_type=FeedbackType(feedback_type),
                        subject=subject,
                        message=message,
                        source="telegram",
                        user_agent=f"Telegram Bot - User: {username}",
                        ip_address="telegram"
                    )
                    
                    db.add(feedback)
                    db.commit()
                    db.refresh(feedback)
                    
                    logger.info(f"Feedback saved: ID={feedback.id}, Type={feedback_type}, User={username}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error saving feedback to DB: {e}")
                    db.rollback()
                    return False
                finally:
                    db.close()
            else:
                # Локальное сохранение в файл
                await self.save_feedback_local(user_id, username, feedback_type, subject, message, user_email, user_telegram)
                return True
                
        except Exception as e:
            logger.error(f"Error in save_feedback: {e}")
            return False
    
    async def save_feedback_local(self, user_id: int, username: str, feedback_type: str,
                                subject: str, message: str, user_email: str = None,
                                user_telegram: str = None):
        """Локальное сохранение обратной связи в файл"""
        
        feedback_data = {
            'id': f"tg_{user_id}_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'username': username,
            'feedback_type': feedback_type,
            'subject': subject,
            'message': message,
            'user_email': user_email,
            'user_telegram': user_telegram,
            'source': 'telegram',
            'created_at': datetime.now().isoformat()
        }
        
        # Сохраняем в JSON файл
        import json
        filename = f"telegram_feedback_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            existing_data = []
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                pass
            
            existing_data.append(feedback_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Feedback saved locally: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving feedback locally: {e}")
    
    def get_feedback_type_name(self, feedback_type: str) -> str:
        """Получение названия типа обратной связи"""
        
        type_names = {
            'question': '❓ Вопрос',
            'suggestion': '💡 Предложение',
            'bug_report': '🐛 Ошибка',
            'feature_request': '🚀 Функция',
            'general': '📝 Общее'
        }
        
        return type_names.get(feedback_type, '📝 Общее')
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ **Произошла ошибка.**\n\n"
                "Пожалуйста, попробуйте позже или используйте другие способы связи.",
                parse_mode='Markdown'
            )
    
    async def run(self):
        """Запуск бота"""
        
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram библиотеки не установлены")
            return
        
        logger.info("Starting Telegram Feedback Bot...")
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram Feedback Bot started successfully!")
            
            # Держим бота запущенным
            await self.application.updater.idle()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

async def main():
    """Основная функция"""
    
    # Токен бота (замените на ваш)
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Пожалуйста, укажите токен бота в переменной BOT_TOKEN")
        return
    
    bot = TelegramFeedbackBot(BOT_TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
