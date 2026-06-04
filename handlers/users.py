import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from supabase import create_client, Client

from keyboards.users import (
    user_keyboard, user_product_keyboard, user_catalog_keyboard,
    user_filter_menu_keyboard, user_filter_price_keyboard, user_filter_size_keyboard
)

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
TABLE_NAME = "dresses"

users_router = Router()

class UserViewState(StatesGroup):
    browsing = State()

# Новые состояния для ввода кастомных фильтров
class FilterSteps(StatesGroup):
    waiting_for_custom_price = State()

# --- СЛОЖНАЯ ДИНАМИЧЕСКАЯ ФИЛЬТРАЦИЯ ДАННЫХ ИЗ SUPABASE ---
async def get_filtered_products(category_name: str | None, state: FSMContext) -> list:
    """Получает платья с учетом выбранных фильтров по цене, размеру и категории"""
    state_data = await state.get_data()
    
    min_p = state_data.get("filter_min_price", 0)
    max_p = state_data.get("filter_max_price", 999999)
    target_size = state_data.get("filter_size") # Например: 44 или None

    # Построение базового запроса к Supabase
    query = supabase.table(TABLE_NAME).select("*")
    
    if category_name:
        query = query.eq("category", category_name)
        
    query = query.gte("price", min_p).lte("price", max_p).order("id")
    response = query.execute()
    
    all_products = response.data
    filtered_products = []
    
    for prod in all_products:
        # 1. Проверяем наличие конкретного размера, если он выбран пользователем
        if target_size:
            count = int(prod.get(f"size_{target_size}", 0) or 0)
            if count > 0:
                filtered_products.append(prod)
        else:
            # 2. Если размер не выбран, проверяем общее наличие хотя бы одного размера
            total_count = sum(int(prod.get(f"size_{size}", 0) or 0) for size in range(40, 68, 2))
            if total_count > 0:
                filtered_products.append(prod)
                
    return filtered_products

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ВЫВОДА КАРТОЧКИ ПОКУПАТЕЛЮ ---
async def send_user_product_card(target, products: list, index: int, state: FSMContext):
    product = products[index]
    
    available_sizes = []
    for size in range(40, 68, 2):
        count = product.get(f"size_{size}", 0)
        if count and int(count) > 0:
            available_sizes.append(str(size))
            
    sizes_str = ", ".join(available_sizes) if available_sizes else "Уточнюйте у менеджера"

    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"💰 Ціна: {product['price']} грн\n"
        f"📏 Доступні розміри: {sizes_str}\n\n"
        f"🌸 Модель {index + 1} із {len(products)}"
    )
    
    kb = user_product_keyboard(product_id=product['id'])
    await state.update_data(u_current_index=index, u_products_list=products)

    if isinstance(target, CallbackQuery):
        try: await target.message.delete()
        except Exception: pass
        await target.message.answer_photo(photo=product['photo'], caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer_photo(photo=product['photo'], caption=text, reply_markup=kb, parse_mode="HTML")

# --- ХЕНДЛЕРЫ КОМАНД ---
@users_router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "Ласкаво просимо до нашого онлайн-магазину чарівних суконь! 👗✨\n\n"
        "Тут ви можете переглянути каталог, підібрати свій розмір за допомогою фільтрів та зробити замовлення.\n\n"
        "✨ **Як зробити замовлення?**\n"
        "1. Перейдіть до Каталогу за кнопкою нижче.\n"
        "2. Оберіть категорію суконь або налаштуйте фільтр цін та розміру.\n"
        "3. Гортайте моделі стрілочками.\n\n"
        "ℹ️ **Наші менеджери:**\n"
        "• Стасик: @NSLegendsRV\n"
        "• Наталія: @Natali_shop_tt\n"
        "УВАГА, У НАШОМУ МАГАЗИНІ ВИКОРИСТОВУЄТЬСЯ ЄВРОПЕЙСКА РОЗМІРНА СІТКА, ДО РОЗМІРУ ДОДАЄТЬСЯ +6"
        "Наприклад розмір плаття 36, ми до нього додаємо +6, тобто розмір буде 42"
    )
    await message.answer(text=welcome_text, reply_markup=user_keyboard(), parse_mode="Markdown")

@users_router.message(Command('help'))
async def cmd_help(message: Message):
    await cmd_start(message)

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ ТЕКСТА И КЛАВИАТУРЫ МЕНЮ ФИЛЬТРОВ ---
async def update_filter_menu_ui(bot, chat_id: int, message_id: int, state: FSMContext):
    """Обновляет интерфейс меню фильтров на основе актуальных данных FSM"""
    data = await state.get_data()
    
    min_p = data.get("filter_min_price")
    max_p = data.get("filter_max_price")
    size_p = data.get("filter_size")
    
    price_str = f"{min_p}-{max_p} грн" if (min_p is not None or max_p is not None) else "Всі"
    size_str = f"{size_p}" if size_p else "Всі"
    
    text = (
        f"⚙️ <b>Панель фільтрації товарів</b>\n\n"
        f"Тут ви можете задати обмеження за бюджетом або знайти сукні вашого розміру.\n"
        f"Поточні налаштування:\n"
        f"• Макс. ціна: <code>{price_str}</code>\n"
        f"• Обраний розмір: <code>{size_str}</code>"
    )
    
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=user_filter_menu_keyboard(price_str, size_str),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка обновления интерфейса фильтров: {e}")

@users_router.callback_query(F.data == "filter_choose_price")
async def filter_choose_price(callback: CallbackQuery):
    await callback.message.edit_text("💰 Оберіть бажаний діапазон цін:", reply_markup=user_filter_price_keyboard())
    await callback.answer()

# --- ВЫБОР И ПРИЕМ КАСТОМНОЙ ЦЕНЫ ---
@users_router.callback_query(F.data.startswith("fprice_"))
async def process_price_selection(callback: CallbackQuery, state: FSMContext):
    if callback.data == "fprice_custom":
        await callback.message.edit_text("⌨️ Введіть максимальну ціну сукні цифрами (наприклад, 2500):")
        await state.set_state(FilterSteps.waiting_for_custom_price)
        await callback.answer()
        return
        
    _, min_p, max_p = callback.data.split("_")
    await state.update_data(filter_min_price=int(min_p), filter_max_price=int(max_p))
    await callback.answer("Ціновий фільтр збережено!", show_alert=False)
    await open_filter_menu(callback, state)

# --- ОТКРЫТИЕ МЕНЮ ФИЛЬТРОВ (ЧЕРЕЗ КНОПКУ) ---
@users_router.callback_query(F.data == "user_filter_menu")
async def open_filter_menu(callback: CallbackQuery, state: FSMContext):
    # Запоминаем ID сообщения, в котором открыты фильтры
    await state.update_data(last_filter_msg_id=callback.message.message_id)
    
    # Просто вызываем функцию обновления интерфейса
    await update_filter_menu_ui(
        bot=callback.bot, 
        chat_id=callback.message.chat.id, 
        message_id=callback.message.message_id, 
        state=state
    )
    await callback.answer()


# --- ПРИЕМ КАСТОМНОЙ ЦЕНЫ ИЗ ТЕКСТА ---
@users_router.message(FilterSteps.waiting_for_custom_price, F.text)
async def process_custom_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть ціну тільки цифрами:")
        return

    # Сохраняем кастомные фильтры в FSM
    await state.update_data(filter_min_price=0, filter_max_price=int(message.text))
    
    data = await state.get_data()
    menu_msg_id = data.get("last_filter_msg_id") # Достаем сохраненный ID меню фильтров
    
    # Сразу чистим за пользователем чат, удаляя его сообщение с цифрами
    try:
        await message.delete()
    except Exception:
        pass

    # Сбрасываем шаг ожидания цены (выходим из состояния)
    await state.set_state(None)
    
    # Если мы знаем, какое сообщение редактировать — обновляем его напрямую через Bot API
    if menu_msg_id:
        await update_filter_menu_ui(
            bot=message.bot, 
            chat_id=message.chat.id, 
            message_id=menu_msg_id, 
            state=state
        )
    else:
        # На всякий пожарный случай, если ID сообщения почему-то потерялся
        await message.answer("Фільтр оновлено! Натисніть кнопку меню знову.")

@users_router.callback_query(F.data == "filter_choose_size")
async def filter_choose_size(callback: CallbackQuery):
    await callback.message.edit_text("📏 Оберіть ваш розмір одягу:", reply_markup=user_filter_size_keyboard())
    await callback.answer()

@users_router.callback_query(F.data.startswith("fsize_"))
async def process_size_selection(callback: CallbackQuery, state: FSMContext):
    size_val = int(callback.data.split("_")[1])
    await state.update_data(filter_size=size_val)
    await callback.answer(f"Розмір {size_val} вибрано!", show_alert=False)
    await open_filter_menu(callback, state)

@users_router.callback_query(F.data == "filter_reset")
async def process_filter_reset(callback: CallbackQuery, state: FSMContext):
    await state.update_data(filter_min_price=None, filter_max_price=None, filter_size=None)
    await callback.answer("Фільтри повністю скинуті ✨", show_alert=True)
    await open_filter_menu(callback, state)

# Логика применения фильтра ко всему каталогу сразу
@users_router.callback_query(F.data == "filter_apply_all")
async def apply_filters_to_all(callback: CallbackQuery, state: FSMContext):
    products = await get_filtered_products(category_name=None, state=state)
    if not products:
        await callback.answer("За вашими фільтрами нічого не знайдено 🤷‍♂️ Спробуйте змінити критерії.", show_alert=True)
        return
        
    await state.set_state(UserViewState.browsing)
    await send_user_product_card(callback, products, 0, state)

# --- КАТЕГОРИИ С УЧЕТОМ СФОРМИРОВАННЫХ ФИЛЬТРОВ ---
@users_router.callback_query(F.data.startswith("usercat_"))
async def admin_category_callback(callback: CallbackQuery, state: FSMContext):
    cat_mapping = {
        "usercat_eve_dresses": "eve_dresses",
        "usercat_prom_dresses": "prom_dresses",
        "usercat_casual_dresses": "casual_dresses"
    }
    category_name = cat_mapping.get(callback.data)
    
    # Теперь запрашиваем товары через наш новый фильтр-модуль
    products = await get_filtered_products(category_name, state)
    
    if not products:
        await callback.answer("З такими фільтрами в цій категорії суконь немає 😔", show_alert=True)
        return

    await state.set_state(UserViewState.browsing)
    await callback.answer()
    await send_user_product_card(callback, products, 0, state)

# --- ПАГИНАЦИЯ (СТРЕЛКИ) ---
@users_router.callback_query(F.data.in_(["u_next", "u_prev", "user_catalog", "return"]))
async def user_navigation_callbacks(callback: CallbackQuery, state: FSMContext):
    if callback.data == "user_catalog":
        await callback.message.answer("Оберіть категорію суконь, яка вас цікавить:", reply_markup=user_catalog_keyboard())
        try: await callback.message.delete()
        except Exception: pass

    elif callback.data == "return":
        try: await callback.message.edit_text("Оберіть дію:", reply_markup=user_keyboard())
        except Exception:
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Оберіть дію:", reply_markup=user_keyboard())

    elif callback.data == "u_next":
        data = await state.get_data()
        products = data.get("u_products_list", [])
        current_index = data.get("u_current_index", 0)
        if current_index + 1 < len(products):
            await send_user_product_card(callback, products, current_index + 1, state)
        else:
            await callback.answer("Це остання модель у цій категорії! 🌸", show_alert=True)

    elif callback.data == "u_prev":
        data = await state.get_data()
        products = data.get("u_products_list", [])
        current_index = data.get("u_current_index", 0)
        if current_index - 1 >= 0:
            await send_user_product_card(callback, products, current_index - 1, state)
        else:
            await callback.answer("Ви на самому початку каталогу!", show_alert=True)
            
    await callback.answer()

@users_router.callback_query(F.data == "user_help")
async def user_help_callback(callback: CallbackQuery):
    await callback.message.answer("З будь-яких питань або для індивідуального замовлення пишіть: @NSLegendsRV")
    await callback.answer()

# Эхо-хендлер для текстового мусора
@users_router.message()
async def echo(message: Message):
    await message.answer(f"Будь ласка, використовуйте меню або команди!", reply_markup=user_keyboard())