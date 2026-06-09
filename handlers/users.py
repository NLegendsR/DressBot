"""
User handlers — memory-efficient version.

Key change: we no longer store the full products list in FSM.
Instead we store only:
  - u_category       (str | None)
  - u_current_index  (int)
  - u_current_id     (int)   ← id of the currently shown product
  - filter_min_price (int)
  - filter_max_price (int)
  - filter_size      (int | None)
  - filter_mode      ("category" | "all")
  - last_filter_msg_id (int)

When the user navigates we fetch a fresh page from Supabase.
Supabase responses are tiny (one row = ~200 bytes) so this costs
almost no network — but saves all the RAM that was used by keeping
entire product lists in MemoryStorage.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.users import (
    user_keyboard, user_product_keyboard, user_catalog_keyboard,
    user_filter_menu_keyboard, user_filter_price_keyboard,
    user_filter_size_keyboard,
)
from db import get_filtered_products

users_router = Router()


class UserViewState(StatesGroup):
    browsing = State()


class FilterSteps(StatesGroup):
    waiting_for_custom_price = State()


# ── helpers ───────────────────────────────────────────────────────────────────

def _size_str(product: dict) -> str:
    sizes = [
        str(s) for s in range(40, 68, 2)
        if int(product.get(f"size_{s}", 0) or 0) > 0
    ]
    return ", ".join(sizes) if sizes else "Уточнюйте у менеджера"


async def _get_products(state: FSMContext) -> list:
    """Re-fetch products using stored filter/category state."""
    data = await state.get_data()
    return await get_filtered_products(
        category=data.get("u_category"),
        min_price=data.get("filter_min_price", 0),
        max_price=data.get("filter_max_price", 999_999),
        target_size=data.get("filter_size"),
    )


async def _send_card(target, state: FSMContext, index: int) -> None:
    """Fetch product list, show card at *index*. Stores only index + id."""
    products = await _get_products(state)
    if not products:
        text = "За вашими фільтрами нічого не знайдено 🤷‍♂️"
        if isinstance(target, CallbackQuery):
            await target.answer(text, show_alert=True)
        else:
            await target.answer(text)
        return

    index = max(0, min(index, len(products) - 1))
    product = products[index]

    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"💰 Ціна: {product['price']} грн\n"
        f"📏 Доступні розміри: {_size_str(product)}\n\n"
        f"🌸 Модель {index + 1} із {len(products)}"
    )
    kb = user_product_keyboard(product_id=product["id"])

    # Store only lightweight data — no full list
    await state.update_data(u_current_index=index, u_current_id=product["id"])

    if isinstance(target, CallbackQuery):
        try:
            await target.message.delete()
        except Exception:
            pass
        await target.message.answer_photo(
            photo=product["photo"], caption=text,
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        await target.answer_photo(
            photo=product["photo"], caption=text,
            reply_markup=kb, parse_mode="HTML"
        )


# ── commands ──────────────────────────────────────────────────────────────────

@users_router.message(CommandStart())
async def cmd_start(message: Message):
    welcome = (
        "Ласкаво просимо до нашого онлайн-магазину чарівних суконь! 👗✨\n\n"
        "Тут ви можете переглянути каталог, підібрати свій розмір за допомогою фільтрів та зробити замовлення.\n\n"
        "✨ **Як зробити замовлення?**\n"
        "1. Перейдіть до Каталогу за кнопкою нижче.\n"
        "2. Оберіть категорію суконь або налаштуйте фільтр цін та розміру.\n"
        "3. Гортайте моделі стрілочками.\n\n"
        "ℹ️ **Наші менеджери:**\n"
        "• Стасик: @NSLegendsRV\n"
        "• Наталія: @Natali_shop_tt\n"
        "<b>УВАГА, У НАШОМУ МАГАЗИНІ ВИКОРИСТОВУЄТЬСЯ ЄВРОПЕЙСКА РОЗМІРНА СІТКА, ДО РОЗМІРУ ДОДАЄТЬСЯ +6</b>\n"
        "Наприклад розмір плаття 36, ми до нього додаємо +6, тобто розмір буде 42"
    )
    await message.answer(text=welcome, reply_markup=user_keyboard(), parse_mode="Markdown")


@users_router.message(Command("help"))
async def cmd_help(message: Message):
    await cmd_start(message)


# ── filter UI ─────────────────────────────────────────────────────────────────

async def _refresh_filter_ui(bot, chat_id: int, msg_id: int, state: FSMContext):
    data = await state.get_data()
    min_p = data.get("filter_min_price")
    max_p = data.get("filter_max_price")
    size_p = data.get("filter_size")

    price_str = f"{min_p}-{max_p} грн" if (min_p is not None or max_p is not None) else "Всі"
    size_str  = str(size_p) if size_p else "Всі"

    text = (
        f"⚙️ <b>Панель фільтрації товарів</b>\n\n"
        f"Поточні налаштування:\n"
        f"• Макс. ціна: <code>{price_str}</code>\n"
        f"• Обраний розмір: <code>{size_str}</code>"
    )
    try:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=text,
            reply_markup=user_filter_menu_keyboard(price_str, size_str),
            parse_mode="HTML",
        )
    except Exception:
        pass


@users_router.callback_query(F.data == "user_filter_menu")
async def open_filter_menu(callback: CallbackQuery, state: FSMContext):
    await state.update_data(last_filter_msg_id=callback.message.message_id)
    await _refresh_filter_ui(callback.bot, callback.message.chat.id,
                              callback.message.message_id, state)
    await callback.answer()


@users_router.callback_query(F.data == "filter_choose_price")
async def filter_choose_price(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 Оберіть бажаний діапазон цін:", reply_markup=user_filter_price_keyboard()
    )
    await callback.answer()


@users_router.callback_query(F.data.startswith("fprice_"))
async def process_price_selection(callback: CallbackQuery, state: FSMContext):
    if callback.data == "fprice_custom":
        await callback.message.edit_text("⌨️ Введіть максимальну ціну сукні цифрами (наприклад, 2500):")
        await state.set_state(FilterSteps.waiting_for_custom_price)
        await callback.answer()
        return

    _, min_p, max_p = callback.data.split("_")
    await state.update_data(filter_min_price=int(min_p), filter_max_price=int(max_p))
    await callback.answer("Ціновий фільтр збережено!")
    await open_filter_menu(callback, state)


@users_router.message(FilterSteps.waiting_for_custom_price, F.text)
async def process_custom_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть ціну тільки цифрами:")
        return

    await state.update_data(filter_min_price=0, filter_max_price=int(message.text))
    data = await state.get_data()
    menu_msg_id = data.get("last_filter_msg_id")

    try:
        await message.delete()
    except Exception:
        pass

    await state.set_state(None)
    if menu_msg_id:
        await _refresh_filter_ui(message.bot, message.chat.id, menu_msg_id, state)
    else:
        await message.answer("Фільтр оновлено! Натисніть кнопку меню знову.")


@users_router.callback_query(F.data == "filter_choose_size")
async def filter_choose_size(callback: CallbackQuery):
    await callback.message.edit_text(
        "📏 Оберіть ваш розмір одягу:", reply_markup=user_filter_size_keyboard()
    )
    await callback.answer()


@users_router.callback_query(F.data.startswith("fsize_"))
async def process_size_selection(callback: CallbackQuery, state: FSMContext):
    size_val = int(callback.data.split("_")[1])
    await state.update_data(filter_size=size_val)
    await callback.answer(f"Розмір {size_val} вибрано!")
    await open_filter_menu(callback, state)


@users_router.callback_query(F.data == "filter_reset")
async def process_filter_reset(callback: CallbackQuery, state: FSMContext):
    await state.update_data(filter_min_price=None, filter_max_price=None, filter_size=None)
    await callback.answer("Фільтри повністю скинуті ✨", show_alert=True)
    await open_filter_menu(callback, state)


@users_router.callback_query(F.data == "filter_apply_all")
async def apply_filters_to_all(callback: CallbackQuery, state: FSMContext):
    await state.update_data(u_category=None)
    await state.set_state(UserViewState.browsing)
    await _send_card(callback, state, 0)


# ── catalog & navigation ──────────────────────────────────────────────────────

@users_router.callback_query(F.data.startswith("usercat_"))
async def user_category_callback(callback: CallbackQuery, state: FSMContext):
    cat_map = {
        "usercat_eve_dresses":    "eve_dresses",
        "usercat_prom_dresses":   "prom_dresses",
        "usercat_casual_dresses": "casual_dresses",
    }
    category = cat_map.get(callback.data)
    await state.update_data(u_category=category)

    # Quick check before entering browse state
    products = await _get_products(state)
    if not products:
        await callback.answer("З такими фільтрами в цій категорії суконь немає 😔", show_alert=True)
        return

    await state.set_state(UserViewState.browsing)
    await callback.answer()
    await _send_card(callback, state, 0)


@users_router.callback_query(F.data.in_(["u_next", "u_prev", "user_catalog", "return"]))
async def user_navigation(callback: CallbackQuery, state: FSMContext):
    if callback.data == "user_catalog":
        await callback.message.answer(
            "Оберіть категорію суконь, яка вас цікавить:",
            reply_markup=user_catalog_keyboard()
        )
        try:
            await callback.message.delete()
        except Exception:
            pass

    elif callback.data == "return":
        try:
            await callback.message.edit_text("Оберіть дію:", reply_markup=user_keyboard())
        except Exception:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer("Оберіть дію:", reply_markup=user_keyboard())

    elif callback.data in ("u_next", "u_prev"):
        data = await state.get_data()
        index = data.get("u_current_index", 0)
        products = await _get_products(state)
        total = len(products)

        if callback.data == "u_next":
            if index + 1 < total:
                await _send_card(callback, state, index + 1)
            else:
                await callback.answer("Це остання модель у цій категорії! 🌸", show_alert=True)
                return
        else:
            if index - 1 >= 0:
                await _send_card(callback, state, index - 1)
            else:
                await callback.answer("Ви на самому початку каталогу!", show_alert=True)
                return

    await callback.answer()


@users_router.callback_query(F.data == "user_help")
async def user_help_callback(callback: CallbackQuery):
    await callback.message.answer("З будь-яких питань або для індивідуального замовлення пишіть: @NSLegendsRV")
    await callback.answer()


@users_router.message()
async def echo(message: Message):
    await message.answer("Будь ласка, використовуйте меню або команди!", reply_markup=user_keyboard())
