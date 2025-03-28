# Telegram Data Analysis Bot

A Telegram bot for data analysis and group management. This bot collects and analyzes data on users and groups, manages groups, forwards messages, and analyzes user interests.

## Features

- **User and Group Statistics**: Collect and analyze data on users and groups, including message counts, active hours, and other metrics.
- **Group Management**: Allow the bot to join, leave, and manage groups.
- **Message Forwarding**: Forward messages from groups to the bot for analysis and storage.
- **Interest Analysis**: Analyze the content of messages to determine users' interests and topics of discussion.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a bot using BotFather and obtain your bot token.

3. Set your bot token as an environment variable:
   ```
   # On Windows
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   
   # On Linux/Mac
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. Run the bot:
   ```
   python bot.py
   ```

## Available Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/stats` - Show statistics
- `/join_group <group_link>` - Join a group
- `/leave_group` - Leave the current group
- `/analyze_interests` - Analyze interests based on messages

## Database

The bot uses SQLite to store data about users, groups, and messages. The database file `telegram_bot.db` will be created automatically when you run the bot for the first time.

## Advanced Interest Analysis

For more advanced interest analysis, consider implementing NLP techniques using libraries like NLTK or spaCy. The current implementation uses a simple keyword-based approach.