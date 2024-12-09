from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_to_cart, orm_add_user, orm_get_user_carts
from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import MenuCallBack
from config import CARD_INFO


class UserStates(StatesGroup):
    phone_number = State()
    custom_model_description = State()


router = Router()
router.message.filter(ChatTypeFilter(["private"]))


@router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup=await get_menu_content(session, level=0, menu_name='main')
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    user = callback.from_user
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None,
    )
    await orm_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer("Товар добавлен в корзину.")


@router.callback_query(MenuCallBack.filter())
async def user_menu(
    callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession, state: FSMContext
):
    if callback_data.menu_name == 'add_to_cart':
        await add_to_cart(callback, callback_data, session)
        return
    elif callback_data.menu_name == 'about':
        await callback.answer()
        await channel_link_message(callback.message)
        return
    elif callback_data.menu_name == 'order':
        await callback.answer()
        await payment_message(callback.message, state)
        return

    media, repli_markup=await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
    )

    if not media:
        return await callback.answer()

    await callback.message.edit_media(media=media, reply_markup=repli_markup)
    await callback.answer()


async def channel_link_message(message: types.Message):
    await message.answer(
        '<b>О насℹ️</b>',
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text='Ссылка на канал', url='https://web.telegram.org/a/#-1002465191855')
        ]]),
        parse_mode='html',
    )


async def payment_message(message: types.Message, state: FSMContext):
    text = 'Для того чтобы мы могли связаться с вами, отправьте нам пожалуйста ваш контакт'
    kb = types.ReplyKeyboardMarkup(keyboard=[[
        types.KeyboardButton(text='☎️Поделиться номером', request_contact=True)
    ]], resize_keyboard=True)

    await message.answer(text=text,reply_markup=kb)

    await state.set_state(UserStates.phone_number)


@router.message(UserStates.phone_number)
async def send_card_info_to_user(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    kb = types.ReplyKeyboardRemove()
    if message.content_type != 'contact':
        return await message.answer('Для продолжения оплаты нам нужен ваш контакт')

    await state.set_state(None)

    text = (f'👤Новый клиент\n\nИмя: {message.chat.full_name}\n'
            f'Юзернейм: @{message.chat.username}\n'
            f'Номер телефона: {message.contact.phone_number}\n\n'
            f'Товары клиента:\n')

    carts = await orm_get_user_carts(session, message.chat.id)
    total_sum = 0

    for cart in carts:
        text += f'- {cart.product.name} X {cart.quantity}\n'
        total_sum += cart.product.price

    text += f'\nСумма заказа: <code>{total_sum}</code>'

    for admin_id in bot.my_admins_list:
        await bot.send_message(admin_id, text)

    text = (f'Ваш контакт мы отправили менеджеру🧑‍💻 В ближайшее время он свяжется с вами\n\n')
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == 'user_custom_model')
async def user_custom_model(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer(
        'Опишите пожалуйста как можно точнее модель, можете приложить фото или ссылку'
    )

    await state.set_state(UserStates.custom_model_description)


@router.message(UserStates.custom_model_description)
async def send_to_manager_custom_model(message: types.Message, state: FSMContext, bot: Bot):
    await state.set_state(None)

    text = ('👤Запрос на кастомную модель\n\n'
            f'Имя: {message.chat.full_name}\n'
            f'Юзернейм: @{message.chat.username}\n\n'
            f'Описание товара:\n')

    if message.content_type == 'text':
        text += f'<blockquote>{message.text}</blockquote>'
    elif message.content_type == 'photo':
        text += f'<blockquote>{message.caption}</blockquote>'
    else:
        await message.answer('Поддерживаются только фото и текст')

    for admin_id in bot.my_admins_list:
        if message.content_type == 'text':
            await bot.send_message(admin_id, text)
        elif message.content_type == 'photo':
            await bot.send_photo(admin_id, message.photo[0].file_id, caption=text)

    await message.answer('Ваш контакт мы отправили менеджеру🧑‍💻 В ближайшее время он свяжется с вами')
