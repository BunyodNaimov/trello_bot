from telebot.handler_backends import StatesGroup, State
from telebot.storage.memory_storage import StateMemoryStorage

state_storage = StateMemoryStorage()


class CreateNewTask(StatesGroup):
    board = State()
    list = State()
    name = State()
    description = State()
    members = State()
    date = State()
    card_id = State()
    label_id = State()
    label_name = State()
    label_color = State()
