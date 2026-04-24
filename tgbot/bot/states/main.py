from aiogram.filters.state import State, StatesGroup


class MessageState(StatesGroup):
    message = State()
    check = State()


class PostAdState(StatesGroup):
    waiting_for_text = State()