from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Перейти до каталогу", callback_data="user_catalog")],
            [InlineKeyboardButton(text="ℹ️ Допомога / Контакти", callback_data="user_help")]
        ]
    )
    return kb

def user_catalog_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Вечірні наряди", callback_data="usercat_eve_dresses"),
                InlineKeyboardButton(text="Випускні", callback_data="usercat_prom_dresses"),
                InlineKeyboardButton(text="Повсякденні", callback_data="usercat_casual_dresses")
            ],
            # Кнопка настройки фильтров
            [
                InlineKeyboardButton(text="⚙️ Налаштувати фільтри", callback_data="user_filter_menu")
            ],
            [
                InlineKeyboardButton(text="Повернутися назад", callback_data="return")
            ]
        ]
    )   
    return kb

# Основное меню фильтров
def user_filter_menu_keyboard(current_price: str, current_size: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"💰 Ціна: {current_price}", callback_data="filter_choose_price"),
                InlineKeyboardButton(text=f"📏 Розмір: {current_size}", callback_data="filter_choose_size")
            ],
            [
                InlineKeyboardButton(text="🚀 Застосувати до ВСІХ суконь", callback_data="filter_apply_all")
            ],
            [
                InlineKeyboardButton(text="🧹 Скинути фільтри", callback_data="filter_reset")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="user_catalog")
            ]
        ]
    )
    return kb

# Выбор ценового диапазона
def user_filter_price_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="До 1500 грн", callback_data="fprice_0_1500")],
            [InlineKeyboardButton(text="1500 - 3000 грн", callback_data="fprice_1500_3000")],
            [InlineKeyboardButton(text="Більше 3000 грн", callback_data="fprice_3000_999999")],
            [InlineKeyboardButton(text="⌨️ Ввести свою ціну", callback_data="fprice_custom")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="user_filter_menu")]
        ]
    )
    return kb

# Генерация сетки размеров от 40 до 66
def user_filter_size_keyboard():
    buttons = []
    # Делаем ряды по 4 кнопки размеров для компактности
    row = []
    for size in range(40, 68, 2):
        row.append(InlineKeyboardButton(text=str(size), callback_data=f"fsize_{size}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="user_filter_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def user_product_keyboard(product_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="u_prev"),
                InlineKeyboardButton(text="➡️", callback_data="u_next")
            ],
            [
                InlineKeyboardButton(
                    text="🙋‍♂️ Замовити у Стасика", 
                    url=f"https://t.me/NSLegendsRV?text=Привіт!_Хочу_замовити_сукню_з_ID_{product_id}"
                ),
                InlineKeyboardButton(
                    text="🙋‍♀️ Замовити у Наталії", 
                    url=f"https://t.me/Natali_shop_tt?text=Привіт!_Хочу_замовити_сукню_з_ID_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="user_catalog")
            ]
        ]
    )
    return kb