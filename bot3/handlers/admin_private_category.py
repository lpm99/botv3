from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin
from database.orm_query import CategoryDAL
from kbds.inline import admin_category_keyboard


class AdminCategoryStates(StatesGroup):
    category_name = State()


router = Router()
router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


@router.message(F.text == 'Категории')
async def admin_category_menu(message: types.Message, session: AsyncSession):
    """Меню категории"""
    text = ('<b>Категории</b>\n\n<i>- Нажмите на категорию, чтобы её <b>удалить</b>🗑\n'
            '- Oсторожно! все товары категории также будут удалены</i>')
    keyboard = await admin_category_keyboard(session, page=0)

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('admin_category_menu'))
async def callback_admin_category_menu(callback: types.CallbackQuery, session: AsyncSession):
    """Меню категории пагинация"""
    page = int(callback.data.split(':')[1])

    text = ('<b>Категории</b>\n\n<i>- Нажмите на категорию, чтобы её <b>удалить</b>🗑 '
            '(осторожно! все товары категории также будут удалены)')
    keyboard = await admin_category_keyboard(session, page)

    await callback.message.edit_reply_markup(text, reply_markup=keyboard)


@router.callback_query(F.data == 'admin_add_category')
async def admin_add_category(callback: types.CallbackQuery, state: FSMContext):
    """Запрос категории"""
    await callback.answer()

    await callback.message.answer('Введите название новой категории')

    await state.set_state(AdminCategoryStates.category_name)


@router.message(AdminCategoryStates.category_name)
async def admin_input_category(message: types.Message, state: FSMContext, session: AsyncSession):
    """Сохранение категории"""
    if message.content_type != 'text':
        return await message.answer('Категория должна быть строкой')

    category_name = message.text

    await CategoryDAL.create(session, name=category_name)

    await message.answer('✅Категория добавлена')

    await admin_category_menu(message, session)


@router.callback_query(F.data.startswith('admin_delete_category'))
async def admin_delete_category(callback: types.CallbackQuery, session: AsyncSession):
    """Подтверждение удаления категории"""
    category_id = int(callback.data.split(':')[1])

    category = await CategoryDAL.read(session, id=category_id)
    if len(category) == 0:
        return await callback.answer('Такая категории уже не существует')
    category = category[0]

    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text='Нет', callback_data='admin_cancel_delete_category'),
        types.InlineKeyboardButton(text='Да', callback_data=f'admin_sure_delete_category:{category.id}'),
    ]])

    await callback.message.edit_text(
        f'Вы уверерны что хотите удалить категорию - {category.name}?',
        reply_markup=kb
    )


@router.callback_query(F.data == 'admin_cancel_delete_category')
async def admin_cancel_delete_category(callback: types.CallbackQuery, session: AsyncSession):
    """Отмена удаления категории"""
    await callback.message.edit_reply_markup(None)

    await admin_category_menu(callback.message, session)


@router.callback_query(F.data.startswith('admin_sure_delete_category'))
async def admin_sure_delete_category(callback: types.CallbackQuery, session: AsyncSession):
    """Удаление категории"""
    await callback.message.edit_reply_markup(None)

    category_id = int(callback.data.split(':')[1])

    await CategoryDAL.delete(session, id=category_id)

    await callback.answer('Категория удалена')

    await admin_category_menu(callback.message, session)
