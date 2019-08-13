from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from django_telegrambot.apps import DjangoTelegramBot

from crawlers.models import Crawler
from crawlers.utils import validate_crawler
from crawlers.utils import validate_task_link
from crawlers.utils import create_task
from crawlers.utils import delete_task
from crawlers.utils import get_tasks
from users.models import User

import logging
logger = logging.getLogger(__name__)

# Commands options
CHALLENGE, CRAWLER, LINK, DELETE_TASK = range(4)


# Start command
def start(bot, update):

    # Check if user exists
    try:
        user = User.objects.get(telegram_id=update.message.chat_id)
    except User.DoesNotExist:
        user = None

    # If user exists
    if user:

        # Say hello
        update.message.reply_text(
            "Hello %s 😀" % update.message.from_user.first_name
        )

        # Print instructions
        help(bot, update)

        return ConversationHandler.END

    else:  # If user not exists

        # Ask user for the secret word
        update.message.reply_text(
            "Secret word?"
        )

        return CHALLENGE


def challenge(bot, update):

    # Check challenge reply
    challenge_reply = update.message.text.lower()

    # If challenge is correct
    if challenge_reply == "jeras":

        # Create a new user
        user = User.objects.get_or_create(telegram_id=update.message.chat_id,
                                          name=update.message.from_user.first_name)

        # Say welcome
        update.message.reply_text(
            "Welcome %s 😀\n"
            "I'm Homie, a bot that will help you finding your next home.\n"
            "This is what I can do for you:"
            % update.message.from_user.first_name
        )

        # Print instructions
        help(bot, update)

    else:  # If challenge is wrong

        # Deny passage and try again
        update.message.reply_text(
            "You shall not pass!"
        )
        update.message.reply_text(
            "Try again /start"
        )

    return ConversationHandler.END


# Help command
def help(bot, update):
    if not valid_user(bot, update):
        return

    # Print help instructions
    update.message.reply_text(
        "/list - list active searches\n"
        "/new - create a new search\n"
        "/delete - delete one search\n"
        "/help - show help instructions"
    )


# No command
def no_command(bot, update):
    if not valid_user(bot, update):
        return

    # Print help instructions
    return help(bot, update)


# New command
def new(bot, update):
    if not valid_user(bot, update):
        return ConversationHandler.END

    # Ask for crawler
    crawler_options = list(Crawler.objects.all().values_list('name', flat=True))
    reply_keyboard = [[x] for x in crawler_options]
    update.message.reply_text(
        "Which site do you want to use?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return CRAWLER


def crawler(bot, update, user_data):
    if not valid_user(bot, update):
        return ConversationHandler.END

    # Validate crawler
    if not validate_crawler(update.message.text):

        update.message.reply_text(
            "Invalid site"
        )

        return ConversationHandler.END

    # Update conversation context
    crawler =  Crawler.objects.get(name__iexact=update.message.text)
    user_data['crawler'] = crawler

    # Ask for link
    update.message.reply_text(
        "1. Go to %s\n"
        "2. Do your search with all the filters you want\n"
        "3. Sort by most recent\n"
        "4. Copy the final link and paste here"
        % crawler.url
    )

    return LINK


def link(bot, update, user_data):
    if not valid_user(bot, update):
        return ConversationHandler.END

    # Validate link
    crawler = user_data['crawler']
    if not validate_task_link(crawler, update.message.text):

        update.message.reply_text(
            "This link is not from %s" % crawler.url
        )

        return ConversationHandler.END

    # Update context
    link = update.message.text
    user_data['link'] = link

    # Create task
    user = User.objects.get(telegram_id=update.message.chat_id)
    task = create_task(user, crawler, link)

    # Confirm new task
    update.message.reply_text(
        "Your new search is ready!\n"
        "Whenever there are new results you will receive them!"
    )

    return ConversationHandler.END


# List command
def list_(bot, update):
    if not valid_user(bot, update):
        return

    # Get user tasks
    user = User.objects.get(telegram_id=update.message.chat_id)
    tasks = get_tasks(user)

    # Build list message
    if tasks:

        message = "You have %s active searches:\n" % len(tasks)

        index = 1
        for task in tasks:
            message += "%s. %s - %s\n" % (index, task.crawler.name, task.search_url)
            index += 1

    else:

        message = "You don't have any active searches"

    # Send tasks list
    update.message.reply_text(
        message
    )


# Delete command
def delete(bot, update):
    if not valid_user(bot, update):
        return

    # Get user tasks
    user = User.objects.get(telegram_id=update.message.chat_id)
    tasks = get_tasks(user)

    if not tasks:

        update.message.reply_text(
            "You don't have any active searches"
        )

        return ConversationHandler.END

    # Build message
    message = "Which search do you eant to delete?\n" \
              "(type the search number)\n"

    index = 1
    for task in tasks:
        message += "%s. %s - %s\n" % (index, task.crawler.name, task.search_url)
        index += 1

    # Send list of tasks
    reply_keyboard = [[str(x)] for x in range(1, len(tasks)+1)]
    update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return DELETE_TASK


def delete_task_command(bot, update):
    if not valid_user(bot, update):
        return

    # Validate selected task to delete
    user = User.objects.get(telegram_id=update.message.chat_id)
    tasks = get_tasks(user)

    try:
        task_index = int(update.message.text) - 1
    except ValueError:
        update.message.reply_text(
            "Invalid search! Make sure you jsut typed the search number"
        )

    if task_index < 0 or task_index >= len(tasks):

        update.message.reply_text(
            "Invalid search! Make sure you jsut typed the search number"
        )

    task = tasks[task_index]

    # Delete task
    delete_task(task)

    # Say confirmation of delete
    update.message.reply_text(
        "Your search was deleted!"
    )

    return ConversationHandler.END


def cancel(bot, update):
    bot.sendMessage(update.message.chat_id, text="cancel")


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    logger.info("Loading handlers for telegram bot")

    # Default dispatcher (this is related to the first bot in settings.DJANGO_TELEGRAMBOT['BOTS'])
    dp = DjangoTelegramBot.dispatcher

    # /start command
    start_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHALLENGE: [MessageHandler(Filters.text, challenge)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(start_conversation_handler)

    # /new command
    create_task_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new)],

        states={
            CRAWLER: [MessageHandler(Filters.text, crawler, pass_user_data=True)],
            LINK: [MessageHandler(Filters.text, link, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(create_task_conversation_handler)

    # /list command
    dp.add_handler(CommandHandler('list', list_))

    # /delete command
    delete_task_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],

        states={
            DELETE_TASK: [MessageHandler(Filters.text, delete_task_command)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(delete_task_conversation_handler)

    # /help command
    dp.add_handler(CommandHandler('help', help))

    # no command
    dp.add_handler(MessageHandler([Filters.text], no_command))

    # log all errors
    dp.add_error_handler(error)


def valid_user(bot, update):

    # Check if this user exists
    try:
        user = User.objects.get(telegram_id=update.message.chat_id)
    except User.DoesNotExist:
        user = None

    if not user:

        # Ask to type start
        update.message.reply_text(
            "Type /start"
        )

        return False

    return True
