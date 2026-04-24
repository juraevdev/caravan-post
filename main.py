"""
Legacy launcher placeholder.

Use `python manage.py runbot` to start the Telegram bot.
This file intentionally avoids embedding runtime credentials.
"""

from tgbot.management.commands.runbot import main


if __name__ == "__main__":
    main()
