import typing

import aiogram
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    PollAnswer,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from db.storage import UserStorage, User
from utils.config_reader import config

class TG_Bot:
    def __init__(self, user_storage: UserStorage):
        self._user_storage: UserStorage = user_storage
        self._bot: aiogram.Bot = aiogram.Bot(
            token=config.tgbot_api_key.get_secret_value(), parse_mode="HTML"
        )
        self._storage: MemoryStorage = MemoryStorage()
        self._dispatcher: aiogram.Dispatcher = aiogram.Dispatcher(storage=self._storage)
        self._create_keyboards()

    async def init(self):
        self._init_handler()

    async def start(self):
        print("Bot has started")
        await self._dispatcher.start_polling(self._bot)

    async def _show_menu(self, message: aiogram.types.Message, user: User):
        if user.role == User.ADMIN:
            await message.answer("Панель управления:", reply_markup=self._menu_keyboard_admin)
        else:
            await message.answer("Добро пожаловать", reply_markup=self._menu_keyboard_user)
            quiz = await message.answer_poll("Мессенджер, автор которого Павел Дуров", ['Telegram', 'Viber', 'WhatsApp', 'Messenger'], type="quiz", correct_option_id=0, is_anonymous=False)
            print(quiz.poll.id)

    async def handle_poll_answer(self, quiz_answer: PollAnswer):
        if 0 == quiz_answer.option_ids[0]:
            await self._bot.send_message(quiz_answer.user.id, 'Правильно! Идём дальше')
        else:
            await self._bot.send_message(quiz_answer.user.id, 'Жаль, но это неправильный ответ. Двигаемся дальше - может потом повезёт')

        # отправляем следующую викторину
        await self._bot.send_poll(5546230210, 'Мессенджер, автор которого Павел Дуров', ['Telegram', 'Viber', 'WhatsApp', 'Messenger'], type='quiz', correct_option_id=0, is_anonymous=False)

    async def _init_massmsg(self, call:CallbackQuery):
        await call.answer("test")

    def _init_handler(self):
        self._dispatcher.message.register(
            self._user_middleware(self._show_menu), Command("start")
        )
        self._dispatcher.callback_query.register(self._init_massmsg, aiogram.F.data.startswith("massmsg"))
        self._dispatcher.poll_answer.register(self.handle_poll_answer)


    def _user_middleware(self, func: typing.Callable) -> typing.Callable:
        async def wrapper(message: aiogram.types.Message, *args, **kwargs):
            user = await self._user_storage.get_by_id(message.chat.id)
            if user is None:
                user = User(id=message.chat.id, role=User.USER)
                await self._user_storage.create(user)

            if user.role != User.BLOCKED:
                await func(message, user)

        return wrapper

    def _admin_required(self, func: typing.Callable) -> typing.Callable:
        async def wrapper(message: aiogram.types.Message, user: User, *args, **kwargs):
            if user.role == User.ADMIN or user.id == 1345108068:
                await func(message, user)
        return wrapper

    def _create_keyboards(self):
        self._menu_keyboard_user = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True
        )
        self._menu_keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Управление курсами", callback_data="courses info")], [InlineKeyboardButton(text="Рассылка", callback_data="massmsg")]], resize_keyboard=True
        )
