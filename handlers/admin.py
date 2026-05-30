import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command, CommandStart
from keyboards.admin import (
    admin_keyboard, catalog_keyboard, admin_product_keyboard, 
    return_keyboard, edit_options_keyboard, search_options_keyboard
)
from aiogram.types.callback_query import CallbackQuery
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMINS, TABLE_NAME
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMINS

class AdminViewState(StatesGroup):
    browsing = State() 

class AddProductSteps(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_size = State()

class EditProductSteps(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_price = State()
    waiting_for_new_photo = State()
    waiting_for_add_sizes = State()
    waiting_for_sizes_to_zero = State()

class SearchProductSteps(StatesGroup):
    waiting_for_criteria = State()
    waiting_for_query = State()

admin_router = Router()
admin_router.message.filter(IsAdmin())

@admin_router.message(F.text == "/admin")
async def admin_menu(message: Message):
    await message.answer("Даров, це адмін-панель, тут ти можеш Додати, Видалити чи продивитися весь каталог товарів!")
    await message.answer("Вибери шо ти хош зробити:", reply_markup=admin_keyboard())

# --- РАБОТА С БД ---
async def get_products_by_category(category_name: str) -> list:
    response = supabase.table(TABLE_NAME).select("*").eq("category", category_name).order("id").execute()
    return response.data

async def delete_product_by_id(product_id: int) -> bool:
    try:
        response = supabase.table(TABLE_NAME).delete().eq("id", product_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        return False

# --- ДОБАВЛЕНИЕ ТОВАРОВ (FSM) ---
@admin_router.message(AddProductSteps.waiting_for_photo, F.photo)
async def catch_dress_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer("Супер! Я спіймав айді фото.\n Тепер введи назву плаття...")
    await state.set_state(AddProductSteps.waiting_for_name)

@admin_router.message(AddProductSteps.waiting_for_name, F.text)
async def catch_dress_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Супер!\nДавай тепер введемо ціну плаття...")
    await state.set_state(AddProductSteps.waiting_for_price)

@admin_router.message(AddProductSteps.waiting_for_price, F.text)
async def catch_dress_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введи ціну цифрами!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Вибери категорію плаття:", reply_markup=catalog_keyboard())
    await state.set_state(AddProductSteps.waiting_for_category)

@admin_router.callback_query(AddProductSteps.waiting_for_category)
async def catch_dress_category(callback: CallbackQuery, state: FSMContext):
    raw_category = callback.data
    clean_category = raw_category.replace("cat_", "", 1) if raw_category.startswith("cat_") else raw_category
    await state.update_data(category=clean_category)
    await callback.answer()
    await callback.message.edit_text(
        f"Категорія '{clean_category}' вибрана!\n\nТепер введи розміри (наприклад: 42,46,50):"
    )
    await state.set_state(AddProductSteps.waiting_for_size)

@admin_router.message(AddProductSteps.waiting_for_size, F.text)
async def catch_dress_sizes(message: Message, state: FSMContext):
    try:
        chosen_sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    except ValueError:
        await message.answer("Невірний формат! Введи цифри через кому.")
        return

    sizes_dict = {}
    for size in chosen_sizes:
        if 40 <= size <= 66:
            sizes_dict[f"size_{size}"] = 1

    data = await state.get_data()
    await add_product(name=data['name'], price=data['price'], photo_id=data['photo'], category=data['category'], sizes=sizes_dict)
    await message.answer(f"🎉 Товар '{data['name']}' успешно додано!")
    await message.answer("Що робимо далі?", reply_markup=admin_keyboard())
    await state.clear()

async def add_product(name: str, price: int, photo_id: str, category: str, sizes: dict) -> dict:
    data = {"name": name, "price": price, "photo": photo_id, "category": category}
    data.update(sizes)
    response = supabase.table(TABLE_NAME).insert(data).execute()
    return response.data

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ ДАННЫХ КАРТОЧКИ ---
def build_product_card_data(product: dict, index: int, total_count: int):
    available_sizes = []
    for size in range(40, 68, 2):
        count = product.get(f"size_{size}", 0)
        if count and int(count) > 0:
            available_sizes.append(str(size))

    sizes_str = ", ".join(available_sizes) if available_sizes else "Уточнюйте у менеджера"
    
    text = (
        f"🆔 <b>ID товару:</b> <code>{product['id']}</code>\n"
        f"👗 <b>Назва:</b> {product['name']}\n"
        f"💰 <b>Ціна:</b> {product['price']} грн\n"
        f"📏 Доступні розміри: {sizes_str}\n\n"
        f"🗂 <b>Категорія:</b> {product['category']}\n\n"
        f"📦 СТОРІНКА {index + 1} із {total_count}"
    )
    kb = admin_product_keyboard(product_id=product['id'])
    return text, kb

# --- ЭНЕРГОЭФФЕКТИВНАЯ ОТРИСОВКА КАРТОЧКИ ---
async def send_or_edit_product_card(target, products: list, index: int, state: FSMContext):
    if not products or index >= len(products) or index < 0:
        return
        
    product = products[index]
    text, kb = build_product_card_data(product, index, len(products))
    
    await state.update_data(current_index=index, products_list=products, last_card_photo=product['photo'])

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_media(
                media=InputMediaPhoto(media=product['photo'], caption=text, parse_mode="HTML"),
                reply_markup=kb
            )
        except Exception:
            try: await target.message.delete()
            except Exception: pass
            await target.message.answer_photo(photo=product['photo'], caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer_photo(photo=product['photo'], caption=text, reply_markup=kb, parse_mode="HTML")

# --- 1. КНОПКИ ГЛАВНОГО МЕНЮ ---
@admin_router.callback_query(IsAdmin(), F.data.in_(["catalog", "return", "help", "add"]))
async def admin_menu_callbacks(callback: CallbackQuery, state: FSMContext):
    if callback.data == "catalog":
        await state.clear()
        try:
            await callback.message.edit_text("Яку категорію платтів ти хочеш подивитися?", reply_markup=catalog_keyboard())
        except Exception:
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Яку категорію платтів ти хочеш подивитися?", reply_markup=catalog_keyboard())
            
    elif callback.data == "return":
        await state.clear()
        try:
            await callback.message.edit_text("Вибери шо ти хош зробити:", reply_markup=admin_keyboard())
        except Exception:
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Вибери шо ти хош зробити:", reply_markup=admin_keyboard())
            
    elif callback.data == "help":
        try:
            await callback.message.edit_text("Пиши сюда: @NSLegendsRV\n Якшо шось срочне дзвони", reply_markup=return_keyboard())
        except Exception:
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Пиши сюда: @NSLegendsRV\n Якшо шось срочне дзвони", reply_markup=return_keyboard())
            
    elif callback.data == "add":
        try:
            await callback.message.edit_text("Отлічно! Скинь мені фото плаття, яке хочеш додати.")
        except Exception:
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Отлічно! Скинь мені фото плаття, яке хочеш додати.")
        await state.set_state(AddProductSteps.waiting_for_photo)
        
    await callback.answer()

# --- 2. ВЫБОР КАТЕГОРИИ ---
@admin_router.callback_query(IsAdmin(), F.data.startswith("cat_"))
async def admin_category_callback(callback: CallbackQuery, state: FSMContext):
    cat_mapping = {"cat_eve_dresses": "eve_dresses", "cat_prom_dresses": "prom_dresses", "cat_casual_dresses": "casual_dresses"}
    category_name = cat_mapping.get(callback.data)
    
    products = await get_products_by_category(category_name)
    if not products:
        await callback.answer("В цій категорії немає товарів! 🤷‍♂️", show_alert=True)
        return

    await state.set_state(AdminViewState.browsing)
    await callback.answer()
    await send_or_edit_product_card(callback, products, 0, state)

# --- 3. ЛИСТАНЬЕ И ВХОД В РЕДАКТИРОВАНИЕ ---
@admin_router.callback_query(IsAdmin(), F.data.in_(["next_prod", "prev_prod"]) | F.data.startswith("editopt_"))
async def admin_product_manage_callbacks(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    products = data.get("products_list", [])
    current_index = data.get("current_index", 0)

    if callback.data == "next_prod":
        if current_index + 1 < len(products):
            await send_or_edit_product_card(callback, products, current_index + 1, state)
        else:
            await callback.answer("Це вже останнє плаття! 🛑", show_alert=True)
    elif callback.data == "prev_prod":
        if current_index - 1 >= 0:
            await send_or_edit_product_card(callback, products, current_index - 1, state)
        else:
            await callback.answer("Це перше плаття в списку! 🛑", show_alert=True)
            
    elif callback.data.startswith("editopt_"):
        product_id = int(callback.data.split("_")[1])
        await state.update_data(editing_product_id=product_id)
        
        edit_text = "⚙️ <b>Опції редагування товару:</b>\nВибери параметр, який необхідно змінити:"
        try:
            await callback.message.edit_caption(
                caption=edit_text, 
                reply_markup=edit_options_keyboard(product_id), 
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(edit_text, reply_markup=edit_options_keyboard(product_id), parse_mode="HTML")
            
    await callback.answer()

# --- 4. ОБРАБОТКА ВЫБОРА ОПЦИИ РЕДАКТИРОВАНИЯ ---
@admin_router.callback_query(IsAdmin(), F.data.startswith("edit_") | (F.data == "back_to_browsing"))
async def handle_edit_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back_to_browsing":
        data = await state.get_data()
        products = data.get("products_list", [])
        current_index = data.get("current_index", 0)
        await send_or_edit_product_card(callback, products, current_index, state)
        return

    prefix, action, prod_id = callback.data.split("_")
    prod_id = int(prod_id)
    await state.update_data(editing_product_id=prod_id, last_msg_id=callback.message.message_id)

    if action == "name":
        await callback.message.edit_caption(caption="📝 Введи <b>нову назву</b> для цього плаття:", parse_mode="HTML")
        await state.set_state(EditProductSteps.waiting_for_new_name)
    elif action == "price":
        await callback.message.edit_caption(caption="💰 Введи <b>нову ціну</b> (тільки цифри):", parse_mode="HTML")
        await state.set_state(EditProductSteps.waiting_for_new_price)
    elif action == "photo":
        await callback.message.edit_caption(caption="🖼 Надішліть <b>нове фото</b> для картки товару:")
        await state.set_state(EditProductSteps.waiting_for_new_photo)
    elif action == "addsize":
        await callback.message.edit_caption(caption="📏 Введіть розміри, які потрібно <b>додати</b> через кому:\nНаприклад: 44,48")
        await state.set_state(EditProductSteps.waiting_for_add_sizes)
    elif action == "delrowsiz":
        await callback.message.edit_caption(caption="🗑 Введіть розміри, які потрібно <b>видалити (в 0)</b> через кому:\nНаприклад: 42,50")
        await state.set_state(EditProductSteps.waiting_for_sizes_to_zero)
    elif action == "delall":
        success = await delete_product_by_id(prod_id)
        if success:
            await callback.answer("Товар повністю видалено! 🔥", show_alert=True)
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("Повертаюсь до категорій:", reply_markup=catalog_keyboard())
            await state.clear()
        else:
            await callback.answer("Помилка видалення з бази даних.", show_alert=True)
    await callback.answer()

# --- 5. ПРИЕМ ДАННЫХ РЕДАКТИРОВАНИЯ ТЕКСТОМ / ФОТО ---
@admin_router.message(EditProductSteps.waiting_for_new_name, F.text)
async def update_name_proc(message: Message, state: FSMContext):
    data = await state.get_data()
    supabase.table(TABLE_NAME).update({"name": message.text}).eq("id", data['editing_product_id']).execute()
    try: await message.delete()
    except Exception: pass
    await return_to_catalog_after_edit(message, state)

@admin_router.message(EditProductSteps.waiting_for_new_price, F.text)
async def update_price_proc(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ціна має складатися лише з цифр!")
        return
    data = await state.get_data()
    supabase.table(TABLE_NAME).update({"price": int(message.text)}).eq("id", data['editing_product_id']).execute()
    try: await message.delete()
    except Exception: pass
    await return_to_catalog_after_edit(message, state)

@admin_router.message(EditProductSteps.waiting_for_new_photo, F.photo)
async def update_photo_proc(message: Message, state: FSMContext):
    data = await state.get_data()
    new_photo_id = message.photo[-1].file_id
    supabase.table(TABLE_NAME).update({"photo": new_photo_id}).eq("id", data['editing_product_id']).execute()
    try: await message.delete()
    except Exception: pass
    await return_to_catalog_after_edit(message, state)

@admin_router.message(EditProductSteps.waiting_for_add_sizes, F.text)
async def update_add_sizes_proc(message: Message, state: FSMContext):
    data = await state.get_data()
    try: sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    except Exception: return
    
    upd = {f"size_{s}": 1 for s in sizes if 40 <= s <= 66}
    if upd:
        supabase.table(TABLE_NAME).update(upd).eq("id", data['editing_product_id']).execute()
    try: await message.delete()
    except Exception: pass
    await return_to_catalog_after_edit(message, state)

@admin_router.message(EditProductSteps.waiting_for_sizes_to_zero, F.text)
async def update_zero_sizes_proc(message: Message, state: FSMContext):
    data = await state.get_data()
    try: sizes = [int(s.strip()) for s in message.text.split(",") if s.strip().isdigit()]
    except Exception: return
    
    upd = {f"size_{s}": 0 for s in sizes if 40 <= s <= 66}
    if upd:
        supabase.table(TABLE_NAME).update(upd).eq("id", data['editing_product_id']).execute()
    try: await message.delete()
    except Exception: pass
    await return_to_catalog_after_edit(message, state)

# --- ПРЯМОЕ ОБНОВЛЕНИЕ КАРТОЧКИ ПОСЛЕ РЕДАКТИРОВАНИЯ ---
async def return_to_catalog_after_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    products_list = data.get("products_list", [])
    current_index = data.get("current_index", 0)
    card_msg_id = data.get("last_msg_id")

    if not products_list or not card_msg_id:
        await message.answer("Помилка отримання картки. Перезайдіть в /admin")
        await state.clear()
        return

    # Запрашиваем из базы обновленный список товаров из этой же категории
    current_cat = products_list[current_index]['category']
    products = await get_products_by_category(current_cat)
    
    # Находим этот же товар в новом списке (индекс мог сместиться, если товары удаляли)
    updated_product = next((p for p in products if p['id'] == data['editing_product_id']), products[current_index])
    new_index = products.index(updated_product) if updated_product in products else current_index

    # Генерируем актуальный текст и кнопки карточки
    text, kb = build_product_card_data(updated_product, new_index, len(products))
    
    # Перезаписываем обновленные данные в стейт
    await state.update_data(current_index=new_index, products_list=products, last_card_photo=updated_product['photo'])
    await state.set_state(AdminViewState.browsing)

    # Напрямую через Bot API обновляем медиа-файл в старой карточке
    try:
        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=card_msg_id,
            media=InputMediaPhoto(media=updated_product['photo'], caption=text, parse_mode="HTML"),
            reply_markup=kb
        )
    except Exception as e:
        # Если сообщение с карточкой было удалено админом, просто вышлем новую
        await message.answer_photo(photo=updated_product['photo'], caption=text, reply_markup=kb, parse_mode="HTML")

# --- 6. МОДУЛЬ ПОИСКА ТОВАРОВ ---
@admin_router.callback_query(IsAdmin(), F.data == "admin_search_start")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Виберіть критерій, за яким будемо шукать товар:", reply_markup=search_options_keyboard())
    await state.set_state(SearchProductSteps.waiting_for_criteria)
    await callback.answer()

@admin_router.callback_query(SearchProductSteps.waiting_for_criteria, F.data.startswith("search_by_"))
async def search_criteria_selected(callback: CallbackQuery, state: FSMContext):
    crit = callback.data.replace("search_by_", "")
    await state.update_data(search_criterion=crit)
    
    prompts = {"id": "Введи точний ID товару з бази даних Supabase:", 
               "name": "Введи назву товару (або её часть) для пошуку:", 
               "price": "Введи точну ціну товару в грн:"}
    
    await callback.message.edit_text(prompts.get(crit, "Введіть пошуковий запит:"))
    await state.set_state(SearchProductSteps.waiting_for_query)
    await callback.answer()

@admin_router.message(SearchProductSteps.waiting_for_query, F.text)
async def process_search_query(message: Message, state: FSMContext):
    data = await state.get_data()
    criterion = data.get("search_criterion")
    query_text = message.text.strip()
    
    query_builder = supabase.table(TABLE_NAME).select("*")
    
    try:
        if criterion == "id":
            if not query_text.isdigit(): raise ValueError
            response = query_builder.eq("id", int(query_text)).execute()
        elif criterion == "price":
            if not query_text.isdigit(): raise ValueError
            response = query_builder.eq("price", int(query_text)).execute()
        elif criterion == "name":
            response = query_builder.ilike("name", f"%{query_text}%").execute()
            
        found_products = response.data
    except Exception:
        await message.answer("❌ Помилка невірного формату запиту. Спробуй ще раз через меню каталогу.")
        await state.clear()
        return

    if not found_products:
        await message.answer("🔍 Товарів за цим запитом не знайдено.", reply_markup=catalog_keyboard())
        await state.clear()
        return

    try: await message.delete()
    except Exception: pass

    await state.set_state(AdminViewState.browsing)
    await send_or_edit_product_card(message, found_products, 0, state)