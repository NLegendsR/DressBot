"""
Admin handlers — memory-efficient version.

FSM stores only:
  - current_index       (int)
  - current_category    (str)
  - editing_product_id  (int)
  - last_msg_id         (int)
  - search_criterion    (str)

No full product lists in state.
"""

from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto, CallbackQuery
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.admin import (
    admin_keyboard, catalog_keyboard, admin_product_keyboard,
    return_keyboard, edit_options_keyboard, search_options_keyboard,
)
from config import ADMINS, TABLE_NAME
from db import (
    supabase,
    get_products_by_category, get_product_by_id,
    add_product, update_product, delete_product, search_products,
    PRODUCT_COLS,
)

admin_router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMINS


admin_router.message.filter(IsAdmin())


class AdminViewState(StatesGroup):
    browsing = State()


class AddProductSteps(StatesGroup):
    waiting_for_photo    = State()
    waiting_for_name     = State()
    waiting_for_price    = State()
    waiting_for_category = State()
    waiting_for_size     = State()


class EditProductSteps(StatesGroup):
    waiting_for_new_name      = State()
    waiting_for_new_price     = State()
    waiting_for_new_photo     = State()
    waiting_for_add_sizes     = State()
    waiting_for_sizes_to_zero = State()


class SearchProductSteps(StatesGroup):
    waiting_for_criteria = State()
    waiting_for_query    = State()


# ── helpers ───────────────────────────────────────────────────────────────────

def _size_str(product: dict) -> str:
    sizes = [
        str(s) for s in range(40, 68, 2)
        if int(product.get(f"size_{s}", 0) or 0) > 0
    ]
    return ", ".join(sizes) if sizes else "Уточнюйте у менеджера"


def _card_text(product: dict, index: int, total: int) -> str:
    return (
        f"🆔 <b>ID товару:</b> <code>{product['id']}</code>\n"
        f"👗 <b>Назва:</b> {product['name']}\n"
        f"💰 <b>Ціна:</b> {product['price']} грн\n"
        f"📏 Доступні розміри: {_size_str(product)}\n\n"
        f"🗂 <b>Категорія:</b> {product['category']}\n\n"
        f"📦 СТОРІНКА {index + 1} із {total}"
    )


async def _get_category_products(state: FSMContext) -> list:
    data = await state.get_data()
    cat = data.get("current_category")
    if not cat:
        return []
    return await get_products_by_category(cat)


async def _show_card(target, state: FSMContext, products: list, index: int):
    """Render a product card. Stores only index + category (no full list)."""
    if not products or not (0 <= index < len(products)):
        return

    product = products[index]
    text = _card_text(product, index, len(products))
    kb   = admin_product_keyboard(product_id=product["id"])

    await state.update_data(
        current_index=index,
        current_category=product["category"],
        editing_product_id=product["id"],
    )

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_media(
                media=InputMediaPhoto(media=product["photo"], caption=text, parse_mode="HTML"),
                reply_markup=kb,
            )
            return
        except Exception:
            try:
                await target.message.delete()
            except Exception:
                pass
    await (target.message if isinstance(target, CallbackQuery) else target).answer_photo(
        photo=product["photo"], caption=text, reply_markup=kb, parse_mode="HTML"
    )


# ── admin menu ────────────────────────────────────────────────────────────────

@admin_router.message(F.text == "/admin")
async def admin_menu(message: Message):
    await message.answer("Даров, це адмін-панель!")
    await message.answer("Вибери шо ти хош зробити:", reply_markup=admin_keyboard())


@admin_router.callback_query(IsAdmin(), F.data.in_(["catalog", "return", "help", "add"]))
async def admin_menu_callbacks(callback: CallbackQuery, state: FSMContext):
    async def _edit(text, kb=None):
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(text, reply_markup=kb)

    if callback.data == "catalog":
        await state.clear()
        await _edit("Яку категорію платтів ти хочеш подивитися?", catalog_keyboard())
    elif callback.data == "return":
        await state.clear()
        await _edit("Вибери шо ти хош зробити:", admin_keyboard())
    elif callback.data == "help":
        await _edit("Пиши сюда: @NSLegendsRV\nЯкшо шось срочне дзвони", return_keyboard())
    elif callback.data == "add":
        await _edit("Отлічно! Скинь мені фото плаття, яке хочеш додати.")
        await state.set_state(AddProductSteps.waiting_for_photo)

    await callback.answer()


# ── category selection ────────────────────────────────────────────────────────

@admin_router.callback_query(IsAdmin(), F.data.startswith("cat_"), ~StateFilter(AddProductSteps.waiting_for_category))
async def admin_category_callback(callback: CallbackQuery, state: FSMContext):
    cat_map = {
        "cat_eve_dresses":    "eve_dresses",
        "cat_prom_dresses":   "prom_dresses",
        "cat_casual_dresses": "casual_dresses",
    }
    category = cat_map.get(callback.data)
    products = await get_products_by_category(category)

    if not products:
        await callback.answer("В цій категорії немає товарів! 🤷‍♂️", show_alert=True)
        return

    await state.set_state(AdminViewState.browsing)
    await state.update_data(current_category=category)
    await callback.answer()
    await _show_card(callback, state, products, 0)


# ── pagination ────────────────────────────────────────────────────────────────

@admin_router.callback_query(IsAdmin(), F.data.in_(["next_prod", "prev_prod"]))
async def admin_paginate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("current_index", 0)
    products = await _get_category_products(state)

    if not products:
        await callback.answer()
        return

    if callback.data == "next_prod":
        new_index = (index + 1) % len(products)
    else:
        new_index = (index - 1) % len(products)

    await _show_card(callback, state, products, new_index)
    await callback.answer()


# ── edit options ──────────────────────────────────────────────────────────────

@admin_router.callback_query(IsAdmin(), F.data.startswith("editopt_"))
async def enter_edit_options(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await state.update_data(editing_product_id=product_id, last_msg_id=callback.message.message_id)

    text = "⚙️ <b>Опції редагування товару:</b>\nВибери параметр, який необхідно змінити:"
    try:
        await callback.message.edit_caption(
            caption=text, reply_markup=edit_options_keyboard(product_id), parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(text, reply_markup=edit_options_keyboard(product_id), parse_mode="HTML")

    await callback.answer()


@admin_router.callback_query(IsAdmin(), F.data.startswith("edit_") | (F.data == "back_to_browsing"))
async def handle_edit_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back_to_browsing":
        products = await _get_category_products(state)
        data     = await state.get_data()
        await _show_card(callback, state, products, data.get("current_index", 0))
        await callback.answer()
        return

    _, action, prod_id = callback.data.split("_")
    prod_id = int(prod_id)
    await state.update_data(editing_product_id=prod_id, last_msg_id=callback.message.message_id)

    prompts = {
        "name":      ("📝 Введи <b>нову назву</b> для цього плаття:", EditProductSteps.waiting_for_new_name),
        "price":     ("💰 Введи <b>нову ціну</b> (тільки цифри):", EditProductSteps.waiting_for_new_price),
        "photo":     ("🖼 Надішліть <b>нове фото</b> для картки товару:", EditProductSteps.waiting_for_new_photo),
        "addsize":   ("📏 Введіть розміри для <b>додавання</b> через кому:\nНаприклад: 44,48", EditProductSteps.waiting_for_add_sizes),
        "delrowsiz": ("🗑 Введіть розміри для <b>видалення (в 0)</b> через кому:\nНаприклад: 42,50", EditProductSteps.waiting_for_sizes_to_zero),
    }

    if action == "delall":
        success = await delete_product(prod_id)
        if success:
            await callback.answer("Товар повністю видалено! 🔥", show_alert=True)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer("Повертаюсь до категорій:", reply_markup=catalog_keyboard())
            await state.clear()
        else:
            await callback.answer("Помилка видалення з бази даних.", show_alert=True)
        await callback.answer()
        return

    caption, next_state = prompts[action]
    try:
        await callback.message.edit_caption(caption=caption, parse_mode="HTML")
    except Exception:
        pass
    await state.set_state(next_state)
    await callback.answer()


# ── edit handlers ─────────────────────────────────────────────────────────────

async def _after_edit(message: Message, state: FSMContext):
    """Refresh the product card after any edit."""
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    prod_id   = data.get("editing_product_id")
    card_msg_id = data.get("last_msg_id")

    product = await get_product_by_id(prod_id)
    if not product or not card_msg_id:
        await message.answer("Помилка отримання картки. Перезайдіть в /admin")
        await state.clear()
        return

    # Re-fetch the full category list to get correct total & index
    products = await get_products_by_category(product["category"])
    index = next((i for i, p in enumerate(products) if p["id"] == prod_id), 0)
    text  = _card_text(product, index, len(products))
    kb    = admin_product_keyboard(product_id=prod_id)

    await state.update_data(current_index=index, current_category=product["category"])
    await state.set_state(AdminViewState.browsing)

    try:
        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=card_msg_id,
            media=InputMediaPhoto(media=product["photo"], caption=text, parse_mode="HTML"),
            reply_markup=kb,
        )
    except Exception:
        await message.answer_photo(
            photo=product["photo"], caption=text, reply_markup=kb, parse_mode="HTML"
        )


@admin_router.message(EditProductSteps.waiting_for_new_name, F.text)
async def update_name(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_product(data["editing_product_id"], {"name": message.text})
    await _after_edit(message, state)


@admin_router.message(EditProductSteps.waiting_for_new_price, F.text)
async def update_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ціна має складатися лише з цифр!")
        return
    data = await state.get_data()
    await update_product(data["editing_product_id"], {"price": int(message.text)})
    await _after_edit(message, state)


@admin_router.message(EditProductSteps.waiting_for_new_photo, F.photo)
async def update_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_product(data["editing_product_id"], {"photo": message.photo[-1].file_id})
    await _after_edit(message, state)


@admin_router.message(EditProductSteps.waiting_for_add_sizes, F.text)
async def update_add_sizes(message: Message, state: FSMContext):
    data  = await state.get_data()
    sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    upd   = {f"size_{s}": 1 for s in sizes if 40 <= s <= 66}
    if upd:
        await update_product(data["editing_product_id"], upd)
    await _after_edit(message, state)


@admin_router.message(EditProductSteps.waiting_for_sizes_to_zero, F.text)
async def update_zero_sizes(message: Message, state: FSMContext):
    data  = await state.get_data()
    sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    upd   = {f"size_{s}": 0 for s in sizes if 40 <= s <= 66}
    if upd:
        await update_product(data["editing_product_id"], upd)
    await _after_edit(message, state)


# ── add product (FSM) ─────────────────────────────────────────────────────────

@admin_router.message(AddProductSteps.waiting_for_photo, F.photo)
async def catch_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Супер! Тепер введи назву плаття...")
    await state.set_state(AddProductSteps.waiting_for_name)


@admin_router.message(AddProductSteps.waiting_for_name, F.text)
async def catch_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Давай тепер введемо ціну плаття...")
    await state.set_state(AddProductSteps.waiting_for_price)


@admin_router.message(AddProductSteps.waiting_for_price, F.text)
async def catch_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введи ціну цифрами!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Вибери категорію плаття:", reply_markup=catalog_keyboard())
    await state.set_state(AddProductSteps.waiting_for_category)


@admin_router.callback_query(AddProductSteps.waiting_for_category)
async def catch_category(callback: CallbackQuery, state: FSMContext):
    raw = callback.data
    cat = raw.removeprefix("cat_")
    await state.update_data(category=cat)
    await callback.answer()
    await callback.message.edit_text(
        f"Категорія '{cat}' вибрана!\n\nТепер введи розміри (наприклад: 42,46,50):"
    )
    await state.set_state(AddProductSteps.waiting_for_size)


@admin_router.message(AddProductSteps.waiting_for_size, F.text)
async def catch_sizes(message: Message, state: FSMContext):
    sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    sizes_dict = {f"size_{s}": 1 for s in sizes if 40 <= s <= 66}

    data = await state.get_data()
    await add_product(
        name=data["name"], price=data["price"],
        photo_id=data["photo"], category=data["category"],
        sizes=sizes_dict,
    )
    await message.answer(f"🎉 Товар '{data['name']}' успішно додано!")
    await message.answer("Що робимо далі?", reply_markup=admin_keyboard())
    await state.clear()


# ── search ────────────────────────────────────────────────────────────────────

@admin_router.callback_query(IsAdmin(), F.data == "admin_search_start")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 Виберіть критерій пошуку:", reply_markup=search_options_keyboard()
    )
    await state.set_state(SearchProductSteps.waiting_for_criteria)
    await callback.answer()


@admin_router.callback_query(SearchProductSteps.waiting_for_criteria, F.data.startswith("search_by_"))
async def search_criteria_selected(callback: CallbackQuery, state: FSMContext):
    crit = callback.data.removeprefix("search_by_")
    await state.update_data(search_criterion=crit)

    prompts = {
        "id":    "Введи точний ID товару:",
        "name":  "Введи назву товару (або її частину):",
        "price": "Введи точну ціну товару в грн:",
    }
    await callback.message.edit_text(prompts.get(crit, "Введіть пошуковий запит:"))
    await state.set_state(SearchProductSteps.waiting_for_query)
    await callback.answer()


@admin_router.message(SearchProductSteps.waiting_for_query, F.text)
async def process_search(message: Message, state: FSMContext):
    data      = await state.get_data()
    criterion = data.get("search_criterion", "name")
    found     = await search_products(criterion, message.text.strip())

    try:
        await message.delete()
    except Exception:
        pass

    if not found:
        await message.answer("🔍 Товарів за цим запитом не знайдено.", reply_markup=catalog_keyboard())
        await state.clear()
        return

    await state.set_state(AdminViewState.browsing)
    await state.update_data(current_category=found[0]["category"])
    await _show_card(message, state, found, 0)