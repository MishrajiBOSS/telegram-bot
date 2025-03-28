#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Bot for data analysis and group management.
Features:
- User and group statistics
- Group management
- Message forwarding
- Interest analysis
"""

import logging
import os
import sqlite3
from datetime import datetime

import pandas as pd
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = 'telegram_bot.db'


def init_db():
    """Initialize the SQLite database with necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        join_date TEXT
    )
    ''')
    
    # Create groups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT,
        join_date TEXT
    )
    ''')
    
    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        group_id INTEGER,
        text TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (group_id) REFERENCES groups (group_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I am a Telegram Bot for data analysis and group management.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /stats - Show statistics
    /join_group <group_link> - Join a group
    /leave_group - Leave the current group
    /analyze_interests - Analyze interests based on messages
    """
    await update.message.reply_text(help_text)


# Statistics functionality
async def collect_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect message data for statistics."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Store user if not exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, join_date) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name, datetime.now().isoformat())
        )
    
    # Store group if not exists and it's a group chat
    if chat.type in ['group', 'supergroup']:
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (chat.id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO groups (group_id, group_name, join_date) VALUES (?, ?, ?)",
                (chat.id, chat.title, datetime.now().isoformat())
            )
    
    # Store message
    cursor.execute(
        "INSERT INTO messages (message_id, user_id, group_id, text, date) VALUES (?, ?, ?, ?, ?)",
        (message.message_id, user.id, chat.id, message.text, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics when the command /stats is issued."""
    conn = sqlite3.connect(DB_PATH)
    
    # Get message counts by user
    user_stats = pd.read_sql_query("""
        SELECT u.username, COUNT(m.message_id) as message_count 
        FROM messages m 
        JOIN users u ON m.user_id = u.user_id 
        GROUP BY m.user_id 
        ORDER BY message_count DESC
    """, conn)
    
    # Get message counts by group
    group_stats = pd.read_sql_query("""
        SELECT g.group_name, COUNT(m.message_id) as message_count 
        FROM messages m 
        JOIN groups g ON m.group_id = g.group_id 
        GROUP BY m.group_id 
        ORDER BY message_count DESC
    """, conn)
    
    # Get active hours
    messages_df = pd.read_sql_query("SELECT date FROM messages", conn)
    messages_df['date'] = pd.to_datetime(messages_df['date'])
    messages_df['hour'] = messages_df['date'].dt.hour
    active_hours = messages_df.groupby('hour').size().reset_index(name='count')
    most_active_hour = active_hours.loc[active_hours['count'].idxmax()]['hour']
    
    conn.close()
    
    # Format statistics message
    stats_message = "📊 Bot Statistics:\n\n"
    
    if not user_stats.empty:
        stats_message += "Top Users by Message Count:\n"
        for _, row in user_stats.head(5).iterrows():
            stats_message += f"- {row['username']}: {row['message_count']} messages\n"
        stats_message += "\n"
    
    if not group_stats.empty:
        stats_message += "Top Groups by Message Count:\n"
        for _, row in group_stats.head(5).iterrows():
            stats_message += f"- {row['group_name']}: {row['message_count']} messages\n"
        stats_message += "\n"
    
    stats_message += f"Most Active Hour: {most_active_hour}:00\n"
    
    await update.message.reply_text(stats_message)


# Group management functionality
async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join a group using the provided link."""
    if not context.args:
        await update.message.reply_text("Please provide a group link or username.")
        return
    
    group_link = context.args[0]
    await update.message.reply_text(f"Attempting to join group: {group_link}")
    # Note: Actual joining would require additional API calls and permissions
    # This is a placeholder for the functionality


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave the current group."""
    chat = update.effective_chat
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    await update.message.reply_text(f"Leaving group: {chat.title}")
    # Note: Actual leaving would require additional API calls
    # This is a placeholder for the functionality


# Message forwarding functionality
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward messages to a designated chat for analysis."""
    # This would typically forward to a specific chat ID or admin
    # For demonstration, we'll just log the message
    message = update.effective_message
    logger.info(f"Message forwarded: {message.text}")
    # Store the message in the database (already done in collect_statistics)


# Interest analysis functionality
async def analyze_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze message content to determine user interests."""
    conn = sqlite3.connect(DB_PATH)
    
    # Get all messages for analysis
    messages_df = pd.read_sql_query("""
        SELECT u.username, m.text 
        FROM messages m 
        JOIN users u ON m.user_id = u.user_id 
        WHERE m.text IS NOT NULL
    """, conn)
    
    conn.close()
    
    if messages_df.empty:
        await update.message.reply_text("Not enough data to analyze interests.")
        return
    
    # Simple keyword-based interest analysis
    # In a real implementation, this would use NLP techniques
    interest_keywords = {
        'technology': ['tech', 'computer', 'software', 'hardware', 'programming', 'code'],
        'sports': ['sport', 'football', 'soccer', 'basketball', 'tennis', 'game'],
        'music': ['music', 'song', 'artist', 'band', 'concert', 'album'],
        'movies': ['movie', 'film', 'cinema', 'actor', 'actress', 'director'],
        'food': ['food', 'recipe', 'cooking', 'restaurant', 'meal', 'dish']
    }
    
    # Count keyword occurrences
    interest_counts = {category: 0 for category in interest_keywords}
    
    for _, row in messages_df.iterrows():
        text = row['text'].lower()
        for category, keywords in interest_keywords.items():
            if any(keyword in text for keyword in keywords):
                interest_counts[category] += 1
    
    # Sort interests by count
    sorted_interests = sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Format interests message
    interests_message = "📈 Interest Analysis:\n\n"
    for category, count in sorted_interests:
        if count > 0:
            interests_message += f"- {category.capitalize()}: {count} mentions\n"
    
    if all(count == 0 for _, count in sorted_interests):
        interests_message += "No specific interests detected yet.\n"
    
    await update.message.reply_text(interests_message)


def main():
    """Start the bot."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize database
    init_db()
    
    # Get bot token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", show_statistics))
    application.add_handler(CommandHandler("join_group", join_group))
    application.add_handler(CommandHandler("leave_group", leave_group))
    application.add_handler(CommandHandler("analyze_interests", analyze_interests))
    
    # Add message handler for collecting statistics and forwarding
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        lambda update, context: collect_statistics(update, context) or forward_message(update, context)
    ))
    
    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()