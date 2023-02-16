import telebot
from environs import Env
from telebot import custom_filters

from states import CreateNewTask
from keyboards import get_inline_boards_btn, get_inline_lists_btn, get_lists_btn, get_members_btn
from trello import TrelloManager
from utils import write_chat_to_csv, check_chat_id_from_csv, get_trello_username_by_chat_id, get_member_tasks_message, \
    check_username_from_csv
import messages

env = Env()
env.read_env()

BOT_TOKEN = env("TELEGRAM_API")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html")


# /Start
@bot.message_handler(commands=["start"])
def welcome(message):
    bot.send_message(message.chat.id, messages.WELCOME_MSG)


# /cancel
@bot.message_handler(commands=["cancel"])
def welcome(message):
    bot.send_message(message.chat.id, messages.CANCEL)


# /Register
@bot.message_handler(commands=["register"])
def register_handler(message):
    if not check_chat_id_from_csv("chats.csv", message.chat.id):
        bot.send_message(message.chat.id, messages.SEND_TRELLO_USERNAME)
        bot.register_next_step_handler(message, get_trello_username)
    else:
        bot.send_message(message.chat.id, messages.ALREADY_REGISTERED)


# Trello username
def get_trello_username(message):
    if check_username_from_csv("chats.csv", message.text):
        bot.send_message(message.chat.id, messages.USER_NAME)
    else:
        write_chat_to_csv("chats.csv", message)
        bot.send_message(message.chat.id, messages.ADD_SUCCESSFULLY)


@bot.message_handler(commands=["boards"])
def get_boards(message):
    if not check_chat_id_from_csv("chats.csv", message.chat.id):
        bot.send_message(message.chat.id, messages.TRELLO_USERNAME_NOT_FOUND)
    else:
        trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
        if trello_username:
            bot.send_message(message.chat.id, messages.SELECT_BOARD,
                             reply_markup=get_inline_boards_btn(trello_username, "show_tasks"))
        else:
            bot.send_message(message.chat.id, messages.TRELLO_USERNAME_NOT_FOUND)


@bot.callback_query_handler(lambda call: call.data.startswith("show_tasks"))
def get_board_lists(call):
    message = call.message
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    board_id = call.data.split("_")[2]
    bot.send_message(
        message.chat.id, "Listni tanlang:", reply_markup=get_inline_lists_btn(trello, board_id, "show_list_tasks")
    )


@bot.callback_query_handler(lambda c: c.data.startswith("show_list_tasks"))
def get_member_cards(call):
    message = call.message
    list_id = call.data.split("_")[3]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    card_data = trello.get_cards_on_a_list(list_id)
    msg = get_member_tasks_message(card_data, trello.get_member_id())
    if msg:
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, messages.NO_TASKS)


# /New
@bot.message_handler(commands=["new"])
def create_new_task(message):
    if not check_chat_id_from_csv("chats.csv", message.chat.id):
        bot.send_message(message.chat.id, messages.TRELLO_USERNAME_NOT_FOUND)
    else:
        trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
        if trello_username:
            bot.send_message(
                message.chat.id, messages.CREATE_TASK,
                reply_markup=get_inline_boards_btn(trello_username, "new_tasks")
            )
            bot.set_state(message.from_user.id, CreateNewTask.board, message.chat.id)
        else:
            bot.send_message(message.chat.id, messages.TRELLO_USERNAME_NOT_FOUND)


@bot.callback_query_handler(lambda c: c.data.startswith("new_tasks"), state=CreateNewTask.board)
def get_new_task_name(call):
    message = call.message
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    board_id = call.data.split("_")[2]
    bot.send_message(
        message.chat.id, "Listni tanlang", reply_markup=get_inline_lists_btn(trello, board_id, "create_list_task")
    )
    bot.set_state(message.from_user.id, CreateNewTask.list, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_board_id"] = board_id


@bot.callback_query_handler(lambda c: c.data.startswith("create_list_task"))
def get_list_id_for_new_task(call):
    message = call.message
    list_id = call.data.split("_")[3]
    name = bot.send_message(message.chat.id, messages.TASK_NAME)
    bot.set_state(message.from_user.id, CreateNewTask.name, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_list_id"] = list_id
        print(data.get("task_board_id"))
    bot.register_next_step_handler(name, get_task_name)


@bot.message_handler(state=CreateNewTask.name)
def get_task_name(message):
    decs = bot.send_message(message.chat.id, messages.TASK_DESC)
    bot.set_state(message.from_user.id, CreateNewTask.description, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_name"] = message.text
        print(data.get("task_board_id"))
    bot.register_next_step_handler(decs, get_task_description)


@bot.message_handler(state=CreateNewTask.description)
def get_task_description(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_desc"] = message.text
        board_id = data["task_board_id"]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    bot.send_message(
        message.chat.id,
        messages.TASK_MEMBERS,
        get_members_btn(trello_username, board_id, "new_task_member")
    )
    bot.set_state(message.from_user.id, CreateNewTask.members, message.chat.id)


@bot.callback_query_handler(lambda c: c.data.startswith("new_task_member_"))
def get_member_id(call):
    message = call.message
    member_id = call.data.split("_")[3]
    bot.send_message(message.chat.id, messages.TASK_LABELS)
    bot.set_state(message.from_user.id, CreateNewTask.members, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["member_id"] = member_id


bot.add_custom_filter(custom_filters.StateFilter(bot))

my_commands = [
    telebot.types.BotCommand("/start", "Boshlash"),
    telebot.types.BotCommand("/register", "Ro'yxatdan o'tish"),
    telebot.types.BotCommand("/new", "Yangi task yaratish"),
    telebot.types.BotCommand("/boards", "Doskalarni ko'rish"),
    telebot.types.BotCommand("/cancel", "Bekor qilish"),
    telebot.types.BotCommand("/help", "Yordam")
]

if __name__ == "__main__":
    print("Started.....")
    bot.set_my_commands(my_commands)
    bot.infinity_polling()
