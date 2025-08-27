import telebot
import sqlite3
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import os
import pandas as pd
import openpyxl



admin_id = [2079770501, 454297480, 8167559033]


FONT_PATH = None
possible_fonts = [
    "arial.ttf", 
]
for font in possible_fonts:
    if os.path.exists(font):
        FONT_PATH = font
        break

BG_COLOR = (255, 255, 255)     
HEADER_COLOR = (52, 152, 219)   
ROW_COLOR = (245, 245, 245)     
TEXT_COLOR = (0, 0, 0)          
BORDER_COLOR = (200, 200, 200)  


bot = telebot.TeleBot("8357900300:AAFswA1QdC7tnYIIVP1pgLSntBl4rcQad6w")



def init_db():
    conn = sqlite3.connect('database.db', isolation_level=None)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS [gameorder] (
        uid INTEGER PRIMARY KEY,
        username TEXT,
        game TEXT,
        platform TEXT,
        area TEXT,
        region TEXT,
        version TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS [serviceorder] (
        uid INTEGER PRIMARY KEY,
        username TEXT,
        service TEXT,
        entrance TEXT
    )''')

   
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS [steamorder] (
        uid INTEGER PRIMARY KEY,
        username TEXT,
        login TEXT,
        count TEXT
    )''')

    conn.commit()
    conn.close()


# создаю пнг табличку
def create_table_image(data, columns, title):
    try:
        font = ImageFont.truetype(FONT_PATH, 16) if FONT_PATH else ImageFont.load_default()
        header_font = ImageFont.truetype(FONT_PATH, 18) if FONT_PATH else ImageFont.load_default()
        title_font = ImageFont.truetype(FONT_PATH, 22) if FONT_PATH else ImageFont.load_default()

        col_widths = []
        for i, col in enumerate(columns):
            max_width = font.getlength(str(col)) + 20
            for row in data:
                text_width = font.getlength(str(row[i] if row[i] else "-")) + 20
                if text_width > max_width:
                    max_width = text_width
            col_widths.append(int(max_width))

        row_height = 40
        table_width = sum(col_widths) + len(columns) + 1
        table_height = (len(data) + 1) * row_height + 80

        img = Image.new("RGB", (table_width, table_height), BG_COLOR)
        draw = ImageDraw.Draw(img)

        draw.text((10, 10), title, font=title_font, fill=HEADER_COLOR)

        y_offset = 50
        x_offset = 0
        for i, col in enumerate(columns):
            draw.rectangle([x_offset, y_offset, x_offset + col_widths[i], y_offset + row_height],
                           fill=HEADER_COLOR, outline=BORDER_COLOR)
            draw.text((x_offset + 5, y_offset + 10), str(col), font=header_font, fill=(255, 255, 255))
            x_offset += col_widths[i]

        for row_idx, row in enumerate(data):
            x_offset = 0
            y_row = y_offset + (row_idx + 1) * row_height
            for i, value in enumerate(row):
                fill_color = ROW_COLOR if row_idx % 2 == 0 else BG_COLOR
                draw.rectangle([x_offset, y_row, x_offset + col_widths[i], y_row + row_height],
                               fill=fill_color, outline=BORDER_COLOR)
                draw.text((x_offset + 5, y_row + 10), str(value) if value else "-", font=font, fill=TEXT_COLOR)
                x_offset += col_widths[i]

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    except Exception as e:
        print("Ошибка создания изображения:", e)
        return None


def create_excel_file(data, columns, filename):
    df = pd.DataFrame(data, columns=columns)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output


@bot.message_handler(commands=['orders'])
def show_orders(message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, game, platform, area, region, version FROM gameorder')
    game_orders = cursor.fetchall()
    cursor.execute('SELECT username, service, entrance FROM serviceorder')
    service_orders = cursor.fetchall()
    conn.close()

    if game_orders:
        game_columns = ["Username", "Game", "Platform", "Area", "Region", "Version"]
        game_img = create_table_image(game_orders, game_columns, "Заказы игр")
        game_excel = create_excel_file(game_orders, game_columns, "game_orders.xlsx")
        bot.send_photo(message.chat.id, game_img, caption="📊 Заказы игр")
        bot.send_document(message.chat.id, game_excel, visible_file_name="game_orders.xlsx")

    if service_orders:
        service_columns = ["Username", "Service", "Entrance"]
        service_img = create_table_image(service_orders, service_columns, "Заказы сервисов")
        service_excel = create_excel_file(service_orders, service_columns, "service_orders.xlsx")
        bot.send_photo(message.chat.id, service_img, caption="📊 Заказы сервисов")
        bot.send_document(message.chat.id, service_excel, visible_file_name="service_orders.xlsx")

    if not game_orders and not service_orders:
        bot.reply_to(message, "Нет заказов для отображения.")


@bot.message_handler(commands=['start'])
def handle_start(message):
    command_parts = message.text.split()
    service_type = command_parts[1] if len(command_parts) > 1 else None

    if service_type == 'games':
        bot.send_message(message.chat.id,
                         "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Какую игру хотите купить?</b>\n"
                         "<b>• На какую платформу? (PC, PlayStation, Xbox, Mobile, Nintendo)</b>\n"
                         "<b>• Какая площадка? (Steam, EA Play, Uplay, Epic Games)</b>\n"
                         "<b>• Какой Регион?</b>\n"
                         "<b>• Версия игры простая или расширенная? (Если есть)</b>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, game_order_create)
    elif service_type == 'services':
        bot.send_message(message.chat.id,
                         "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Какой сервис хотите приобрести?</b>\n"
                         "<b>• С входом на ваш аккаунт или вам создать новый?</b>\n",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, service_order_create)

    elif service_type == 'steam':
        bot.send_message(message.chat.id,
                         "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Свой логин STEAM</b>\n"
                         "Сумму пополнения STEAM кошелька в рублях\n",
                         parse__mode='HTML')
        bot.register_next_step_handler(message, steam_order_create)
    else:
        lobby(message)



def lobby(message):
    text = """
    <b> Привет, друг 😃 Я менеджер магазина K·Shop.</b>

    <b>Если хочешь что-то приобрести - смело выбирай на кнопках ниже 👇</b>
    """
    if message.from_user.id in admin_id:

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🛒 Купить игру", callback_data="buy_game")
        btn2 = types.InlineKeyboardButton("🛒 Купить сервис", callback_data="buy_service")
        btn3 = types.InlineKeyboardButton("🛒 Пополнить баланс STEAM", callback_data="buy_steam")
        admbtn = types.InlineKeyboardButton("🛠️ Войти в панель админа", callback_data="admin")
        markup.row(btn3)
        markup.row(btn1, btn2)
        markup.row(admbtn)

        with open("welcome.jpg", "rb") as photo:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup
            )
    else:

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🛒 Купить игру", callback_data="buy_game")
        btn2 = types.InlineKeyboardButton("🛒 Купить сервис", callback_data="buy_service")
        btn3 = types.InlineKeyboardButton("🛒 Пополнить баланс STEAM", callback_data="buy_steam")
        markup.row(btn3)
        markup.row(btn1, btn2)

        with open("welcome.jpg", "rb") as photo:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup
            )


def callback_lobby(call):
    text = """
    <b> Привет, друг 😃 Я менеджер магазина K·Shop.</b>

    <b>Если хочешь что-то приобрести - смело выбирай на кнопках ниже 👇</b>
    """
    if call.from_user.id in admin_id:

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🛒 Купить игру", callback_data="buy_game")
        btn2 = types.InlineKeyboardButton("🛒 Купить сервис", callback_data="buy_service")
        btn3 = types.InlineKeyboardButton("🛒 Пополнить баланс STEAM", callback_data="buy_steam")
        admbtn = types.InlineKeyboardButton("🛠️ Войти в панель админа", callback_data="admin")
        markup.row(btn3)
        markup.row(btn1, btn2)
        markup.row(admbtn)

        with open("welcome.jpg", "rb") as photo:
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup
            )
    else:

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🛒 Купить игру", callback_data="buy_game")
        btn2 = types.InlineKeyboardButton("🛒 Купить сервис", callback_data="buy_service")
        btn3 = types.InlineKeyboardButton("🛒 Пополнить баланс STEAM", callback_data="buy_steam")
        markup.row(btn3)
        markup.row(btn1, btn2)

        with open("welcome.jpg", "rb") as photo:
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup
            )



def game_order_create(message):
    order = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(order) == 5:
        game, platform, area, region, version = order

        uid = message.from_user.id
        uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO [gameorder] (uid, username, game, platform, region, area, version)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        ''', (uid, uname, game, platform, region, area, version))
        conn.commit()
        conn.close()

        bot.reply_to(message, "Ваш заказ был принят, в ближайшее время мы обработаем его.")
        lobby(message)
    else:
        bot.reply_to(message, "Пожалуйста, ответьте на все 5 вопросов, каждый с новой строки.")



def service_order_create(message):
    order = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(order) == 2:
        service, entrance = order

        uid = message.from_user.id
        uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO [serviceorder] (uid, username, service, entrance)
        VALUES(?, ?, ?, ?)
        ''', (uid, uname, service, entrance))
        conn.commit()
        conn.close()

        bot.reply_to(message, "Ваш заказ был принят, в ближайшее время мы обработаем его.")
        lobby(message)
    else:
        bot.reply_to(message, "Пожалуйста, ответьте на все 2 вопроса, каждый с новой строки.")


def steam_order_create(message):
    order = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(order) == 2:
        login, count = order

        uid = message.from_user.id
        uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO [steamorder] (uid, username, login, count)
        VALUES(?, ?, ?, ?)
        ''', (uid, uname, login, count))
        conn.commit()
        conn.close()

        bot.reply_to(message, "Ваш заказ был принят, в ближайшее время мы обработаем его.")
        lobby(message)
    else:
        bot.reply_to(message, "Пожалуйста, ответьте на оба вопроса, каждый с новой строки.")




def show_orders_callback(call):
    if call.from_user.id in admin_id:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT username, game, platform, area, region, version FROM [gameorder]')
        game_orders = cursor.fetchall()

        cursor.execute('SELECT username, service, entrance FROM [serviceorder]')
        service_orders = cursor.fetchall()

        conn.close()

        if game_orders:
            game_columns = ["Username", "Game", "Platform", "Area", "Region", "Version"]
            game_img = create_table_image(game_orders, game_columns, "Заказы игр")
            bot.send_photo(call.message.chat.id, game_img, caption="📊 Заказы игр")

        if service_orders:
            service_columns = ["Username", "Service", "Entrance"]
            service_img = create_table_image(service_orders, service_columns, "Заказы сервисов")
            bot.send_photo(call.message.chat.id, service_img, caption="📊 Заказы сервисов")

        if not game_orders and not service_orders:
            bot.send_message(call.message.chat.id, "Нет заказов для отображения.")
    else:
        bot.answer_callback_query(call.id, "У вас нет прав администратора")

def delete_bd_callback(call):
    if call.from_user.id in admin_id:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM [gameorder]")
        cursor.execute("DELETE FROM [serviceorder]")
        cursor.execute("DELETE FROM [steamorder]")

        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, "База данных очищена")
    else:
        bot.answer_callback_query(call.id, "У вас нет прав администратора")

# обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    if call.data == "buy_game":
        bot.send_message(call.message.chat.id,
                         "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Какую игру хотите купить?</b>\n"
                         "<b>• На какую платформу? (PC, PlayStation, Xbox, Mobile, Nintendo)</b>\n"
                         "<b>• Какая площадка? (Steam, EA Play, Uplay, Epic Games)</b>\n"
                         "<b>• Какой Регион?</b>\n"
                         "<b>• Версия игры простая или расширенная? (Если есть)</b>",
                         parse_mode='HTML')
        bot.register_next_step_handler(call.message, game_order_create)
    elif call.data == "buy_service":
        bot.send_message(call.message.chat.id,
                         "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Какой сервис хотите приобрести?</b>\n"
                         "<b>• С входом на ваш аккаунт или вам создать новый?</b>\n",
                         parse_mode='HTML')
        bot.register_next_step_handler(call.message, service_order_create)

    elif call.data == 'buy_steam':
        bot.send_message(call.message.chat.id,
                            "Приветствую, напишите, пожалуйста, следующее:\n\n<b>• Свой логин STEAM</b>\n"
                            "Сумму пополнения STEAM кошелька в рублях\n",
                            parse_mode='HTML')
        bot.register_next_step_handler(call.message, steam_order_create)

    elif call.data == "admin":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("📊 Заказы", callback_data="order")
        btn2 = types.InlineKeyboardButton("🗑️ Очистить базу данных", callback_data="cleardb")
        backbtn = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_lobby")
        markup.row(btn1, btn2)
        markup.row(backbtn)
        bot.send_message(call.message.chat.id,"<b>Панель администратора</b>", parse_mode='HTML', reply_markup=markup)

    elif call.data == "order":
        show_orders_callback(call)
    
    elif call.data == "cleardb":
        delete_bd_callback(call)

    elif call.data == "back_to_lobby":
        callback_lobby(call)



if __name__ == '__main__':
    init_db()
    bot.infinity_polling()