from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton)

from utils import get_trello_username_by_chat_id
from trello import TrelloManager


def get_inline_boards_btn(trello_username, action):
    inline_boards_btn = InlineKeyboardMarkup()
    boards = TrelloManager(trello_username).get_boards()
    if len(boards) % 2 == 0:
        last_board = None
    else:
        last_board = boards.pop()
    for i in range(0, len(boards) - 1, 2):
        inline_boards_btn.add(
            InlineKeyboardButton(
                boards[i].get("name"), callback_data=f"{action}_{boards[i].get('id')}"
            ),
            InlineKeyboardButton(
                boards[i + 1].get("name"), callback_data=f"{action}_{boards[i + 1].get('id')}"
            ),
        )
    if last_board:
        inline_boards_btn.add(
            InlineKeyboardButton(last_board.get("name"), callback_data=f"{action}_{last_board.get('id')}")
        )
    return inline_boards_btn


def get_lists_btn(trello, board_id):
    lists_btn = ReplyKeyboardMarkup()
    lists = trello.get_lists_on_a_board(board_id)
    if len(lists) % 2 == 0:
        last_list = None
    else:
        last_list = lists.pop()
    for list_index in range(0, len(lists) - 1, 2):
        lists_btn.add(
            KeyboardButton(lists[list_index].get("name")),
            KeyboardButton(lists[list_index + 1].get("name"))
        )
    if last_list:
        lists_btn.add(KeyboardButton(last_list.get("name")))
    return lists_btn


def get_inline_lists_btn(trello, board_id, action):
    lists_inline_btn = InlineKeyboardMarkup()
    lists = trello.get_lists_on_a_board(board_id)
    if len(lists) % 2 == 0:
        last_list = None
    else:
        last_list = lists.pop()
    for i in range(0, len(lists) - 1, 2):
        lists_inline_btn.add(
            InlineKeyboardButton(
                lists[i].get("name"),
                callback_data=f'{action}_{lists[i].get("id")}'
            ),
            InlineKeyboardButton(
                lists[i + 1].get("name"),
                callback_data=f'{action}_{lists[i + 1].get("id")}'
            )
        )
    if last_list:
        lists_inline_btn.add(
            InlineKeyboardButton(
                last_list.get("name"),
                callback_data=f'{action}_{last_list.get("id")}'
            )
        )
    return lists_inline_btn


def get_members_btn(trello_username, board_id, action):
    members = TrelloManager(trello_username).get_board_members(board_id)
    members_id = []
    for i in members:
        members_id.append(i.get("idMember"))
    data = []
    for i in members_id:
        data.append(TrelloManager(trello_username).get_fullname_in_members(i))
    members_btn = InlineKeyboardMarkup()
    if len(data) % 2 == 0:
        last_member = None
    else:
        last_member = data.pop()
    for i in range(0, len(data) - 1, 2):
        members_btn.add(
            InlineKeyboardButton(
                data[i].get("fullName"),
                callback_data=f'{action}_{data[i].get("id")}'
            ),
            InlineKeyboardButton(
                data[i + 1].get("fullName"),
                callback_data=f'{action}_{data[i + 1].get("id")}'
            ),
        )
    if last_member:
        members_btn.add(
            InlineKeyboardButton(
                last_member.get("fullName"), callback_data=f'{action}_{last_member.get("id")}'
            )
        )
    return members_btn


def get_inline_btn_labels(user_name, board_id, action):
    btn = TrelloManager(user_name).get_labels_board(board_id)
    btn_labels = []
    for i in btn:
        if i.get("name"):
            btn_labels.append(i)
    inline_btn = InlineKeyboardMarkup()
    if len(btn_labels) % 2 == 0:
        last_btn = None
    else:
        last_btn = btn_labels.pop()

    for i in range(0, len(btn_labels) - 1, 2):
        inline_btn.add(
            InlineKeyboardButton(btn_labels[i].get("name"),
                                 callback_data=f"{action}_{btn_labels[i].get('id')}"),
            InlineKeyboardButton(btn_labels[i + 1].get("name"),
                                 callback_data=f"{action}_{btn_labels[i + 1].get('id')}")
        )

    if last_btn:
        inline_btn.add(
            InlineKeyboardButton(InlineKeyboardButton(last_btn[0].get("name"),
                                                      callback_data=f"{action}_{last_btn[0].get('id')}"))
        )
    return inline_btn


def get_inline_cards_btn(chat_id, list_id, action):
    trello_username = get_trello_username_by_chat_id("../chats.csv", chat_id)
    data = TrelloManager(trello_username).get_cards_on_a_list(list_id)
    cards_btn = []
    for i in data:
        dic = {
            f"{i.get('name')}": f"{i.get('id')}"
        }
        cards_btn.append(dic)
    inline_cards_btn = InlineKeyboardMarkup()

    if len(cards_btn) % 2 == 0:
        btn = None
    else:
        btn = cards_btn.pop()
    for i in range(0, len(cards_btn) - 1, 2):
        inline_cards_btn.add(
            InlineKeyboardButton(list(cards_btn[i].keys())[0],
                                 callback_data=f"{action}_{list(cards_btn[i].values())[0]}"),
            InlineKeyboardButton(list(cards_btn[i + 1].keys())[0],
                                 callback_data=f"{action}_{list(cards_btn[i + 1].values())[0]}")
        )
    if btn:
        print(btn)
        inline_cards_btn.add(
            InlineKeyboardButton(list(btn.keys())[0],
                                 callback_data=f"{action}_{list(btn.values())[0]}")
        )
    return inline_cards_btn


def get_inline_color_btn(action):
    btn = {
        "🟥": "red",
        "🟩": "green",
        "🟨": "yellow",
        "🟪": "purple",
        "🟦": "blue",
        "🟧": "orange",
        }
    color_inline_btn = InlineKeyboardMarkup()
    for i in range(0, len(btn)-1, 2):
        color_inline_btn.add(
            InlineKeyboardButton(list(btn.keys())[i], callback_data=f"{action}_{list(btn.values())[i]}"),
            InlineKeyboardButton(list(btn.keys())[i+1], callback_data=f"{action}_{list(btn.values())[i+1]}")
        )
    return color_inline_btn
