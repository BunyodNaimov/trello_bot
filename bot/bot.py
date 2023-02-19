import telebot
import messages

from environs import Env
from telebot import custom_filters
from states import CreateNewTask, state_storage
from keyboards import get_inline_boards_btn, get_inline_lists_btn, get_members_btn, get_inline_btn_labels, \
    get_inline_cards_btn, get_inline_color_btn
from trello import TrelloManager
from utils import write_chat_to_csv, check_chat_id_from_csv, get_trello_username_by_chat_id, get_member_tasks_message, \
    check_username_from_csv

env = Env()
env.read_env()

BOT_TOKEN = env("TELEGRAM_API")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html", state_storage=state_storage)


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


def get_trello_username(message):
    if check_username_from_csv("chats.csv", message.text):
        bot.send_message(message.chat.id, messages.USER_NAME)
    else:
        write_chat_to_csv("chats.csv", message)
        bot.send_message(message.chat.id, messages.ADD_SUCCESSFULLY)


# /Boards
@bot.message_handler(commands=["boards"])
def get_boards(message):
    bot.set_chat_menu_button(message.chat.id)
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
        message.chat.id, messages.SELECT_LIST, reply_markup=get_inline_lists_btn(trello, board_id, "show_list_tasks")
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


# / New Boards
@bot.message_handler(commands=["new_board"])
def new_board_name(message):
    bot.send_message(message.chat.id, messages.BOARD_NAME)
    bot.register_next_step_handler(message, create_new_board)


def create_new_board(message):
    board_name = message.text
    user_name = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(user_name)
    trello.create_new_boards(board_name)
    bot.send_message(message.chat.id, messages.BOARD_ADD)


# / New Label
@bot.message_handler(commands=["new_label"])
def get_board_id(message):
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    bot.send_message(message.chat.id, "Doskani tanlang",
                     reply_markup=get_inline_boards_btn(trello_username, "board_id"))
    bot.set_state(message.from_user.id, CreateNewTask.board, message.chat.id)


@bot.callback_query_handler(lambda c: c.data.startswith("board_id_"))
def get_label_name(call):
    message = call.message
    board_id = call.data.split("_")[2]
    msg = bot.send_message(message.chat.id, "Label nomini kiriting: ")
    bot.set_state(call.from_user.id, CreateNewTask.label_name, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["idBoard"] = board_id
    bot.register_next_step_handler(msg, get_label_color)


def get_label_color(message):
    bot.send_message(message.chat.id, "Label rangini tanlang yoki kiriting: ",
                     reply_markup=get_inline_color_btn("color_btn"))
    bot.set_state(message.from_user.id, CreateNewTask.label_color, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["name"] = message.text


@bot.callback_query_handler(lambda c: c.data.startswith("color_btn"))
def create_new_label(call):
    message = call.message
    label_color = call.data.split("_")[2]
    user_name = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(user_name)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["color"] = label_color
        params = {
            "name": {data["name"]},
            "color": {data["color"]},
            "idBoard": {data["idBoard"]}
        }
        trello.create_new_labels(params)
    bot.send_message(message.chat.id, messages.LABEL_ADD)
    bot.delete_state(message.from_user.id, message.chat.id)


# /Add Label in cards
@bot.message_handler(commands=["add_label_to_card"])
def select_board(message):
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    bot.send_message(message.chat.id, messages.SELECT_BOARD,
                     reply_markup=get_inline_boards_btn(trello_username, "select_board"))
    bot.set_state(message.from_user.id, CreateNewTask.board, message.chat.id)


@bot.callback_query_handler(lambda c: c.data.startswith("select_board"))
def get_boards_label(call):
    message = call.message
    board_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    trello.get_labels_board(board_id)
    bot.send_message(message.chat.id, "Listni tanlang:",
                     reply_markup=get_inline_lists_btn(trello, board_id, "select_list")
                     )
    bot.set_state(call.from_user.id, CreateNewTask.list, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["board_id"] = board_id


@bot.callback_query_handler(lambda c: c.data.startswith("select_list"))
def get_list_in_board_label(call):
    message = call.message
    list_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username).get_cards_on_a_list(list_id)
    bot.send_message(message.chat.id, messages.SELECT_CARD,
                     reply_markup=get_inline_cards_btn(message.chat.id, list_id, "cards"))
    bot.set_state(call.from_user.id, CreateNewTask.card_id, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["list_id"] = list_id


@bot.callback_query_handler(lambda c: c.data.startswith("cards_"))
def get_card_in_list_label(call):
    message = call.message
    card_id = call.data.split("_")[1]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["card_id"] = card_id
        bot.send_message(message.chat.id, messages.TASK_LABELS,
                         reply_markup=get_inline_btn_labels(trello_username, data["board_id"], "label_name"))


@bot.callback_query_handler(lambda c: c.data.startswith("label_name"))
def add_label_to_card(call):
    message = call.message
    label_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["label_id"] = label_id
        trello.add_label_to_card(data["card_id"], data["label_id"])
    bot.send_message(call.from_user.id, messages.LABEL_ADD)
    bot.delete_state(call.from_user.id)


# /New card
@bot.message_handler(commands=["new_card"])
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
    bot.set_state(message.from_user.id, state=CreateNewTask.list)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["task_board_id"] = board_id


@bot.callback_query_handler(lambda c: c.data.startswith("create_list_task"))
def get_list_id_for_new_task(call):
    message = call.message
    list_id = call.data.split("_")[3]
    msg = bot.send_message(message.chat.id, messages.TASK_NAME)
    bot.set_state(message.from_user.id, state=CreateNewTask.name)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["task_list_id"] = list_id
    bot.register_next_step_handler(msg, get_task_name)


def get_task_name(message):
    bot.send_message(message.chat.id, messages.TASK_DESC)
    bot.set_state(message.from_user.id, state=CreateNewTask.description)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_name"] = message.text


@bot.message_handler(state=CreateNewTask.description, content_types=["text"])
def get_task_description(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["task_desc"] = message.text
        board_id = data["task_board_id"]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    bot.send_message(
        message.chat.id,
        messages.TASK_MEMBERS,
        reply_markup=get_members_btn(trello_username, board_id, "new_task_member")
    )
    bot.set_state(message.from_user.id, CreateNewTask.members, message.chat.id)


@bot.callback_query_handler(lambda c: c.data.startswith("new_task_member_"))
def get_member_id(call):
    message = call.message
    member_id = call.data.split("_")[3]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    bot.set_state(call.from_user.id, CreateNewTask.members, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["member_id"] = member_id
        param = {
            "board": data["task_board_id"],
            "idList": data["task_list_id"],
            "name": data["task_name"],
            "description": data["task_desc"],
            "members": data["member_id"],
        }
        trello.create_new_card(param)
    bot.send_message(call.from_user.id, messages.CARD_ADD)
    bot.delete_state(call.from_user.id, message.chat.id)


# /Add a Member to a Card
@bot.message_handler(commands=["member_to_card"])
def get_board_member(message):
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    bot.send_message(message.chat.id, messages.SELECT_BOARD,
                     reply_markup=get_inline_boards_btn(trello_username, "board_member"))
    bot.set_state(message.from_user.id, CreateNewTask.board, message.chat.id)


@bot.callback_query_handler(lambda c: c.data.startswith("board_member"))
def get_list_member(call):
    message = call.message
    board_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    bot.send_message(message.chat.id, messages.SELECT_LIST,
                     reply_markup=get_inline_lists_btn(trello, board_id, "list_member"))
    bot.set_state(call.from_user, CreateNewTask.list, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["board_id"] = board_id


@bot.callback_query_handler(lambda c: c.data.startswith("list_member"))
def get_card_member(call):
    message = call.message
    list_id = call.data.split("_")[2]
    bot.send_message(message.chat.id, messages.SELECT_CARD,
                     reply_markup=get_inline_cards_btn(message.chat.id, list_id, "card_member"))
    bot.set_state(call.from_user, CreateNewTask.card_id, message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["list_id"] = list_id


@bot.callback_query_handler(lambda c: c.data.startswith("card_member"))
def get_select_member(call):
    message = call.message
    card_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        data["card_id"] = card_id
        bot.send_message(message.chat.id, messages.SELECT_MEMBER,
                         reply_markup=get_members_btn(trello_username, data["board_id"], "select_member"))


@bot.callback_query_handler(lambda c: c.data.startswith("select_member"))
def add_member_to_card(call):
    message = call.message
    member_id = call.data.split("_")[2]
    trello_username = get_trello_username_by_chat_id("chats.csv", message.chat.id)
    trello = TrelloManager(trello_username)
    with bot.retrieve_data(call.from_user.id, message.chat.id) as data:
        trello.add_a_member_to_card(data["card_id"], member_id)
    bot.send_message(message.chat.id, messages.MEMBER_ADD)
    bot.delete_state(call.from_user.id, message.chat.id)


bot.add_custom_filter(custom_filters.StateFilter(bot))

my_commands = [
    telebot.types.BotCommand("/start", "Boshlash"),
    telebot.types.BotCommand("/register", "Ro'yxatdan o'tish"),
    telebot.types.BotCommand("/boards", "Doskalarni ko'rish"),
    telebot.types.BotCommand("/new_board", "Yangi doska yaratish"),
    telebot.types.BotCommand("/new_card", "Yangi card yaratish"),
    telebot.types.BotCommand("/member_to_card", "Cardga member qo'shish"),
    telebot.types.BotCommand("/new_label", "Yangi label yaratish"),
    telebot.types.BotCommand("/add_label_to_card", "Cardga label biriktirish"),
    telebot.types.BotCommand("/cancel", "Bekor qilish"),
    telebot.types.BotCommand("/help", "Yordam"),

]

if __name__ == "__main__":
    print("Started.....")
    bot.set_my_commands(my_commands)
    bot.infinity_polling()
