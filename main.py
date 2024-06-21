import telebot
import sqlite3
import os

# Вставьте свой токен сюда
API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

def get_db_connection(chat_id):
    db_path = f'{chat_id}.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        game_nik TEXT
    )
    ''')
    conn.commit()
    return conn, cursor

# Функция для проверки администраторских прав пользователя
def is_admin(chat_id, user_id):
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет! Добавьте меня в группу и используйте команду /reg, чтобы зарегистрировать пользователя с его ником в игре.')

# Обработчик команды /reg
@bot.message_handler(commands=['reg'])
def register_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем администраторские права пользователя
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return
    
    conn, cursor = get_db_connection(chat_id)
    
    command_parts = message.text.split(' ')
    if len(command_parts) != 3:
        bot.reply_to(message, 'Используйте команду /reg в формате: /reg <username> <nik>')
        return
    
    username = command_parts[1]
    game_nik = command_parts[2]

    # Проверяем, зарегистрирован ли уже пользователь с таким username
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        bot.reply_to(message, f"Пользователь @{username} уже зарегистрирован.")
    else:
        # Сохраняем данные в базу данных
        cursor.execute('INSERT INTO users (username, game_nik) VALUES (?, ?)', (username, game_nik))
        conn.commit()
        
        # Ответ на сообщение
        response = f"Пользователь: @{username}\nНик в игре: *{game_nik}*."
        bot.reply_to(message, response, parse_mode='Markdown')

    # Закрываем соединение
    conn.close()

# Обработчик команды /nik
@bot.message_handler(commands=['nik'])
def save_nik(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        conn, cursor = get_db_connection(chat_id)
        
        replied_message = message.reply_to_message
        username = replied_message.from_user.username
        
        # Проверяем, чтобы бот не реагировал на свои сообщения
        if username == bot.get_me().username:
            return
        
        # Извлекаем данные из базы данных
        cursor.execute('SELECT game_nik FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            game_nik = result[0]
            response = f"Пользователь: @{username}\nНик в игре: *{game_nik}*."
        else:
            response = f"Пользователь: @{username} не зарегистрирован."
        
        conn.close()

        bot.reply_to(message, response, parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Пожалуйста, используйте эту команду как ответ на сообщение пользователя.')

# Обработчик команды /del
@bot.message_handler(commands=['del'])
def delete_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем администраторские права пользователя
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return
    
    conn, cursor = get_db_connection(chat_id)
    
    command_parts = message.text.split(' ')
    if len(command_parts) != 2:
        bot.reply_to(message, 'Используйте команду /del в формате: /del <username>')
        return
    
    username = command_parts[1]

    # Проверяем наличие пользователя в базе данных
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result:
        # Удаляем пользователя из базы данных
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        bot.reply_to(message, f"Информация о пользователе @{username} удалена из базы данных.")
    else:
        bot.reply_to(message, f"Пользователь @{username} не зарегистрирован в базе данных.")

    # Закрываем соединение
    conn.close()

# Обработчик всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Бот игнорирует все сообщения, кроме команд /start, /reg, /nik и /del
    pass

# Запуск бота
bot.polling()
