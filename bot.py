import os
import typing
import random

import aiofiles
import aiogram
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import State, StatesGroup
from aiogram.types import (
    PollAnswer,
    FSInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from db.storage import UserStorage, User
from utils.config_reader import config
from utils.parser import (
    get_course_data,
    get_courses_names,
    get_course_info,
    delete_course,
)


class QuizState(StatesGroup):
    quiz = State()


class MassMsgState(StatesGroup):
    message = State()


class CreateNewCourse(StatesGroup):
    name = State()
    info = State()
    input_data = State()
    content = State()


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
            await message.answer("Меню:", reply_markup=self._menu_keyboard_admin)
        else:
            await message.answer(
                "Добро пожаловать", reply_markup=self._menu_keyboard_user
            )

    async def _show_inline_menu(self, call: CallbackQuery, user: User):
        if user.role == User.ADMIN:
            await call.message.edit_text(
                "Меню:", reply_markup=self._menu_keyboard_admin
            )
        else:
            await call.message.edit_text(
                "Добро пожаловать", reply_markup=self._menu_keyboard_user
            )

    async def _new_course_name(self, call: CallbackQuery, state: FSMContext):
        await call.message.edit_text(
            "Введите название нового курса", reply_markup=self._cancel_keyboard
        )
        await state.set_state(CreateNewCourse.name)

    async def _new_course_info(self, message: aiogram.types.Message, state: FSMContext):
        await state.update_data(course_name=message.text.strip())
        await message.answer(
            "Введите описание нового курса", reply_markup=self._cancel_keyboard
        )
        await state.set_state(CreateNewCourse.info)

    async def _new_course_input_data(
        self, message: aiogram.types.Message, state: FSMContext
    ):
        await state.update_data(course_info=message.text.strip())
        await message.answer(
            "Пришлите входные данные нового курса, если их нет отправьте ",
            reply_markup=self._cancel_keyboard,
        )
        await state.set_state(CreateNewCourse.content)

    async def _new_course_content(
        self, message: aiogram.types.Message, state: FSMContext
    ):
        await state.update_data(course_info=message.text.strip())
        await message.answer(
            "Пришлите файл-скрипт нового курса", reply_markup=self._cancel_keyboard
        )
        await state.set_state(CreateNewCourse.content)

    async def _create_new_course(
        self, message: aiogram.types.Message, state: FSMContext
    ):
        state_data = await state.get_data()
        os.mkdir(f"courses/{state_data['course_name']}")
        with open(
            f"courses/{state_data['course_name']}/info.txt", "w", encoding="utf-8"
        ) as info_file:
            info_file.write(state_data["course_info"])
        await self._bot.download(
            message.document,
            destination=f"courses/{state_data['course_name']}/text.txt",
        )
        await message.answer(
            "Курс успешно создан!", reply_markup=self._to_menu_keyboard_user
        )

    async def _show_courses(self, call: CallbackQuery, user: User):
        if user.role == User.ADMIN:
            await call.message.edit_text(
                "Панель управления курсами:", reply_markup=self._courses_keyboard_admin
            )
        else:
            courses_names = get_courses_names()
            courses_buttons = [
                [
                    InlineKeyboardButton(
                        text=course_name, callback_data="?c" + course_name
                    )
                ]
                for course_name in courses_names
            ]
            courses_buttons.append(
                [InlineKeyboardButton(text="Меню", callback_data="show_menu")]
            )
            courses_keyboard_user = InlineKeyboardMarkup(
                inline_keyboard=courses_buttons, resize_keyboard=True
            )
            await call.message.edit_text(
                "Сейчас доступны следующие курсы:", reply_markup=courses_keyboard_user
            )

    async def _courses_lookup(self, call: CallbackQuery, user: User):
        courses_names = get_courses_names()
        courses_buttons = [
            [InlineKeyboardButton(text=course_name, callback_data="?c" + course_name)]
            for course_name in courses_names
        ]
        courses_buttons.append(
            [InlineKeyboardButton(text="Меню", callback_data="show_menu")]
        )
        courses_keyboard_user = InlineKeyboardMarkup(
            inline_keyboard=courses_buttons, resize_keyboard=True
        )
        await call.message.edit_text(
            "Сейчас запущены эти курсы", reply_markup=courses_keyboard_user
        )  # TODO сделать stash курсов, чтобы их можно было скрывать

    async def _show_course_info(self, call: CallbackQuery, user: User):
        course_name = call.data[2:]
        if user.role == User.ADMIN:
            course_keyb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Протестировать курс", callback_data="?b" + course_name
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Файл", callback_data="?f" + course_name
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Удалить курс", callback_data="?a" + course_name
                        )
                    ],
                    [InlineKeyboardButton(text="Меню", callback_data="show_menu")],
                ],
                resize_keyboard=True,
            )
            await call.message.edit_text(
                f"Курс {course_name}\n\n{get_course_info(course_name)}",
                reply_markup=course_keyb,
            )
        else:
            course_keyb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Купить курс", callback_data="?b" + course_name
                        )
                    ],
                    [InlineKeyboardButton(text="Меню", callback_data="show_menu")],
                ],
                resize_keyboard=True,
            )
            await call.message.edit_text(
                f"Курс {course_name}\n\n{get_course_info(course_name)}",
                reply_markup=course_keyb,
            )

    async def _ask_delete_course(self, call: CallbackQuery):
        course_name = call.data[2:]
        confirm_keyb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data="?d" + course_name)],
                [InlineKeyboardButton(text="ОТМЕНА", callback_data="cancel")],
            ],
            resize_keyboard=True,
        )
        await call.message.edit_text(
            f"Вы уверены что хотите удалить этот курс:\n\nКурс {course_name}\n\n{get_course_info(course_name)}",
            reply_markup=confirm_keyb,
        )

    async def _get_course_file(self, call: CallbackQuery):
        course_name = call.data[2:]
        file = FSInputFile(f"courses/{course_name}/text.txt")
        await call.message.answer_document(
            file, caption=course_name, reply_markup=self._to_menu_keyboard_user
        )

    async def _delete_course(self, call: CallbackQuery):
        course_name = call.data[2:]
        delete_course(course_name)
        await call.message.answer(
            "Курс успешно удалён!", reply_markup=self._to_menu_keyboard_user
        )

    async def _start_course(self, call: CallbackQuery, state: FSMContext):
        course_name = call.data[2:]
        course_data = get_course_data(course_name)
        i = 0
        if isinstance(course_data[i], str) and course_data[i].startswith("Listening"):
            i += 1
        elif isinstance(course_data[i], str) and course_data[i].startswith("Reading"):
            await call.message.answer(course_data[i][8:])
            i += 1
        random.shuffle(course_data[i]["answers"])
        correct_option_id = course_data[i]["answers"].index(course_data[i]["correct"])
        await call.message.answer_poll(
            course_data[i]["question"],
            course_data[i]["answers"],
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False,
        )
        await state.set_state(QuizState.quiz)
        await state.update_data(course_name=course_name)
        await state.update_data(correct_option_id=correct_option_id)
        await state.update_data(course_data=course_data[i + 1 :])

    async def handle_poll_answer(self, quiz_answer: PollAnswer, state: FSMContext):
        state_data = await state.get_data()
        course_data = state_data["course_data"]
        if len(course_data) == 0:
            await self._bot.send_message(
                quiz_answer.user.id,
                "Поздравляем! Курс пройден. Вы всегда можете вернуться к нему",
                reply_markup=self._to_menu_keyboard_user,
            )
        else:
            if (
                state_data["correct_option_id"] == quiz_answer.option_ids[0]
            ):  # TODO Комментарии к ответам
                await self._bot.send_message(
                    quiz_answer.user.id, "Правильно! Идём дальше"
                )
            else:
                await self._bot.send_message(
                    quiz_answer.user.id,
                    "Жаль, но это неправильный ответ.",
                )
            i = 0
            if isinstance(course_data[i], str) and course_data[i].startswith(
                "Listening"
            ):
                await self._bot.send_message(quiz_answer.user.id, "Listening")
                await self._bot.send_audio(
                    quiz_answer.user.id,
                    aiogram.types.input_file.FSInputFile(
                        f"courses/{state_data['course_name']}/{course_data[i][10:].strip()}"
                    ),
                )
                i += 1
            elif isinstance(course_data[i], str) and course_data[i].startswith(
                "Reading"
            ):
                await self._bot.send_message(quiz_answer.user.id, "Reading")
                await self._bot.send_message(quiz_answer.user.id, course_data[i][8:])
                i += 1
            random.shuffle(course_data[i]["answers"])
            correct_option_id = course_data[i]["answers"].index(
                course_data[i]["correct"]
            )
            await self._bot.send_poll(
                quiz_answer.user.id,
                course_data[i]["question"],
                course_data[i]["answers"],
                type="quiz",
                correct_option_id=correct_option_id,
                is_anonymous=False,
            )
            await state.update_data(correct_option_id=correct_option_id)
            await state.update_data(course_data=course_data[i + 1 :])

    async def _init_massmsg(self, call: CallbackQuery, state: FSMContext):
        await call.message.edit_text(
            "Введите сообщение для рассылки", reply_markup=self._cancel_keyboard
        )
        await state.set_state(MassMsgState.message)

    async def _send_massmsg(self, message: aiogram.types.Message, state: FSMContext):
        all_users = await self._user_storage.get_all_members()
        count = 0
        for user in all_users:
            try:
                await self._bot.copy_message(
                    user.id, message.from_user.id, message.message_id
                )
                count += 1
            except aiogram.exceptions.TelegramForbiddenError:
                pass
        await state.clear()
        await message.answer(
            f"Сообщение успешно разослано {count} из {len(all_users)} пользователей",
            reply_markup=self._menu_keyboard_admin,
        )

    async def _cancel(self, call: CallbackQuery, state: FSMContext):
        if state is not None:
            await state.clear()
            await call.answer("Отмена")
        await self._bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id
        )
        user = await self._user_storage.get_by_id(call.from_user.id)
        await self._show_menu(call.message, user)

    def _init_handler(self):
        self._dispatcher.message.register(
            self._user_middleware(self._show_menu), Command("start")
        )
        self._dispatcher.callback_query.register(
            self._callback_user_middleware(self._show_courses),
            aiogram.F.data.startswith("courses_menu"),
        )
        self._dispatcher.callback_query.register(
            self._callback_user_middleware(self._show_inline_menu),
            aiogram.F.data.startswith("show_menu"),
        )
        self._dispatcher.callback_query.register(
            self._callback_user_middleware(self._show_course_info),
            aiogram.F.data.startswith("?c"),
        )
        self._dispatcher.callback_query.register(
            self._start_course, aiogram.F.data.startswith("?b")
        )
        self._dispatcher.callback_query.register(
            self._ask_delete_course, aiogram.F.data.startswith("?a")
        )
        self._dispatcher.callback_query.register(
            self._delete_course, aiogram.F.data.startswith("?d")
        )
        self._dispatcher.callback_query.register(
            self._get_course_file, aiogram.F.data.startswith("?f")
        )
        self._dispatcher.callback_query.register(
            self._callback_user_middleware(self._courses_lookup),
            aiogram.F.data.startswith("courses_lookup"),
        )
        self._dispatcher.callback_query.register(
            self._new_course_name, aiogram.F.data.startswith("upload_new_course")
        )
        self._dispatcher.callback_query.register(
            self._init_massmsg, aiogram.F.data.startswith("massmsg")
        )
        self._dispatcher.callback_query.register(
            self._cancel, aiogram.F.data.startswith("cancel")
        )

        self._dispatcher.message.register(self._new_course_info, CreateNewCourse.name)
        self._dispatcher.message.register(
            self._new_course_content, CreateNewCourse.info
        )
        self._dispatcher.message.register(
            self._create_new_course, CreateNewCourse.content
        )

        self._dispatcher.message.register(self._send_massmsg, MassMsgState.message)

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

    def _callback_user_middleware(self, func: typing.Callable) -> typing.Callable:
        async def wrapper(call: CallbackQuery, *args, **kwargs):
            user = await self._user_storage.get_by_id(call.from_user.id)
            if user is None:
                user = User(id=call.from_user.id, role=User.USER)
                await self._user_storage.create(user)

            if user.role != User.BLOCKED:
                await func(call, user)

        return wrapper

    def _admin_required(self, func: typing.Callable) -> typing.Callable:
        async def wrapper(message: aiogram.types.Message, user: User, *args, **kwargs):
            if user.role == User.ADMIN or user.id == 1345108068:
                await func(message, user)

        return wrapper

    def _create_keyboards(self):
        self._to_menu_keyboard_user = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="show_menu")]
            ],
            resize_keyboard=True,
        )
        self._menu_keyboard_user = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Курсы", callback_data="courses_menu")]
            ],
            resize_keyboard=True,
        )
        self._menu_keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Управление курсами", callback_data="courses_menu"
                    )
                ],
                [InlineKeyboardButton(text="Рассылка", callback_data="massmsg")],
            ],
            resize_keyboard=True,
        )
        self._courses_keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Обзор курсов", callback_data="courses_lookup"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Загрузить", callback_data="upload_new_course"
                    )
                ],
                [InlineKeyboardButton(text="Меню", callback_data="show_menu")],
            ],
            resize_keyboard=True,
        )

        self._cancel_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="ОТМЕНА", callback_data="cancel")]
            ],
            resize_keyboard=True,
        )
