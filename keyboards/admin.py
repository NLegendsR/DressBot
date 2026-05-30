from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗂 Каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="➕ Добавити товар", callback_data="add")],
            [InlineKeyboardButton(text="❓ Питання?", callback_data="help")]
        ]
    )
    return kb

def catalog_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Вечірні наряди", callback_data="cat_eve_dresses"),
                InlineKeyboardButton(text="Випускні", callback_data="cat_prom_dresses"),
                InlineKeyboardButton(text="Повсякденні", callback_data="cat_casual_dresses")
            ],
            [
                InlineKeyboardButton(text="🔍 Пошук товару", callback_data="admin_search_start")
            ],
            [
                InlineKeyboardButton(text="🔙 Повернутися назад", callback_data="return")
            ]
        ]
    )   
    return kb

# Чистая клавиатура под карточкой товара
def admin_product_keyboard(product_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️Попередня", callback_data="prev_prod"),
                InlineKeyboardButton(text="➡️Наступне", callback_data="next_prod")
            ],
            [
                InlineKeyboardButton(text="⚙️ Редагувати товар", callback_data=f"editopt_{product_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="catalog")
            ]
        ]
    )
    return kb

# Меню опций редактирования (Вызывается по кнопке Редагувати)
def edit_options_keyboard(product_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Назву", callback_data=f"edit_name_{product_id}"),
                InlineKeyboardButton(text="💰 Ціну", callback_data=f"edit_price_{product_id}")
            ],
            [
                InlineKeyboardButton(text="🖼 Фото", callback_data=f"edit_photo_{product_id}"),
                InlineKeyboardButton(text="📏 Додати розміри", callback_data=f"edit_addsize_{product_id}")
            ],
            [
                InlineKeyboardButton(text="🗑 Видалити розміри (в 0)", callback_data=f"edit_delrowsiz_{product_id}")
            ],
            [
                InlineKeyboardButton(text="💥 ВИДАЛИТИ ВСЕ ПЛАТТЯ", callback_data=f"edit_delall_{product_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Скасувати", callback_data="back_to_browsing")
            ]
        ]
    )
    return kb

# Выбор критерия поиска
def search_options_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆔 За ID", callback_data="search_by_id")],
            [InlineKeyboardButton(text="🔤 За назвою", callback_data="search_by_name")],
            [InlineKeyboardButton(text="💵 За ціною", callback_data="search_by_price")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
        ]
    )
    return kb

def return_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Повернутися назад", callback_data="return")]
        ]
    )
    return kb