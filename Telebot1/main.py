from telebot.types import ReplyKeyboardRemove
from datetime import datetime, date
from telebot import TeleBot, types
import psycopg2
import requests

bot = TeleBot('7209349514:AAGXBHcIOJRNhKrWmm8eErdBiR5BhADw8kg')

commands = [
    types.BotCommand('/start', 'Барои оғоз кардани бот'),
    types.BotCommand('/help', 'Кумакрасони ва тарзи истифодаи бот'),
]
bot.set_my_commands(commands)

def connection_database():
    connection = psycopg2.connect(
        database="telegr_bot",
        user="postgres",
        host="localhost",
        password="1234",
        port=5432
    )
    return connection

def close_connection(conn, cur):
    cur.close()
    conn.close()

def create_user_table():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
                CREATE TABLE IF NOT EXISTS USERS (
                USER_ID VARCHAR(100) PRIMARY KEY,
                FIRST_NAME VARCHAR(30) NOT NULL,
                LAST_NAME VARCHAR(30) NOT NULL,
                USERNAME VARCHAR(60)
                )""")
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def create_arrival_table():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS arrivals (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100),
            arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_to_go TIMESTAMP,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (USER_ID)
            );
        """)
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def create_feedback_table():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100),
            feedback_text TEXT,
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (USER_ID)
            );
        """)
        conn.commit()
    except Exception as e:
        print(f'Error creating feedback table: {str(e)}')
    finally:
        close_connection(conn, cur)

def add_users(user_id, first_name, last_name, username):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO USERS (USER_ID, FIRST_NAME, LAST_NAME, USERNAME) VALUES (%s, %s, %s, %s)
            ON CONFLICT (USER_ID) DO NOTHING""", (str(user_id), first_name, last_name, username))
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def change_arrival_today(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        today = date.today()
        cur.execute("""
            SELECT arrival_time FROM arrivals
            WHERE user_id = %s AND date = %s
        """, (str(user_id), today))
        result = cur.fetchone()
        return result
    except Exception as e:
        print(f'Error: {str(e)}')
        return None
    finally:
        close_connection(conn, cur)

def add_arrival_time(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        existing_time = change_arrival_today(user_id)
        if existing_time:
            bot.send_message(user_id, f'Вақти омадани шумо илова карда шуда буд: {existing_time[0]}. Мехоҳед таъғир диҳед?')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn_ha = types.KeyboardButton('Ҳа')
            btn_ne = types.KeyboardButton('Не')
            markup.add(btn_ha, btn_ne)
            bot.send_message(user_id, 'Тасдиқ кунед Ҳа ё Не:', reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(user_id, update_arrival)
        else:
            arrival_time = datetime.now()
            cur.execute("""
                INSERT INTO arrivals (user_id, arrival_time, date) VALUES (%s, %s, %s)
            """, (str(user_id), arrival_time, arrival_time.date()))
            conn.commit()
            bot.send_message(user_id, f'Вақти омадан шумо илова карда шуд: {arrival_time}')

    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def update_arrival(message):
    user_id = message.chat.id
    if message.text == 'Ҳа':
        arrival_time = datetime.now()
        conn = connection_database()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE arrivals SET arrival_time = %s WHERE user_id = %s AND date = %s
            """, (arrival_time, str(user_id), arrival_time.date()))
            conn.commit()
            bot.send_message(user_id, f'Вақти омадан шумо иваз карда шуд: {arrival_time}')
            send_message_bot(message.chat.id)
        except Exception as e:
            print(f'Error: {str(e)}')
        finally:
            close_connection(conn, cur)
    elif message.text == 'Не':
        bot.send_message(user_id, 'Ташаккур! Мо вақтатонро иваз намекунем.')

def check_time_to_go(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        today = date.today()
        cur.execute("""
            SELECT time_to_go FROM arrivals
            WHERE user_id = %s AND date = %s
        """, (str(user_id), today))
        result = cur.fetchone()
        return result
    except Exception as e:
        print(f'Error: {str(e)}')
        return None
    finally:
        close_connection(conn, cur)

def add_time_to_go(user_id):
    existing_time = check_time_to_go(user_id)
    if existing_time and existing_time[0] is not None:
        bot.send_message(user_id, 'Шумо метавонед вақти рафтанро танҳо як маротиба дар як рӯз ворид кунед.')
    else:
        try:
            conn = connection_database()
            cur = conn.cursor()
            time_to_go = datetime.now()
            cur.execute("""
                UPDATE arrivals SET time_to_go = %s
                WHERE user_id = %s AND date = %s
            """, (time_to_go, str(user_id), time_to_go.date()))
            conn.commit()
            bot.send_message(user_id, f'Вақти рафтани шумо сабт шуд: {time_to_go}')
        except Exception as e:
            print(f'Error adding departure time: {str(e)}')
        finally:
            close_connection(conn, cur)

def add_feedback(user_id, feedback_text):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO feedback (user_id, feedback_text) VALUES (%s, %s)
        """, (str(user_id), feedback_text))
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def ask_for_feedback(user_id):
    msg = bot.send_message(user_id, "Лутфан, Фикру андешаҳо нисбат ба боти худро нависед:")
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    user_id = message.chat.id
    feedback_text = message.text
    add_feedback(user_id, feedback_text)
    bot.send_message(user_id, "Ташаккур барои Фикру андешаҳо нисбат ба ботятон!")
    send_message_bot(user_id)  

@bot.message_handler(commands=['start'])
def start(message):
    create_user_table()
    create_arrival_table()
    create_feedback_table()
    
    user_id = message.chat.id
    first_name = message.chat.first_name or ''
    last_name = message.chat.last_name or ''
    username = message.chat.username or ''

    if not first_name:
        msg = bot.send_message(user_id, 'Номатонро дохил кунед')
        bot.register_next_step_handler(msg, get_first_name, last_name, username)
    elif not last_name:
        msg = bot.send_message(user_id, 'Насабатонро дохил кунед')
        bot.register_next_step_handler(msg, get_last_name, first_name, username)
    elif not username:
        msg = bot.send_message(user_id, 'User name-атонро дохил кунед')
        bot.register_next_step_handler(msg, get_username, first_name, last_name)
    else:
        add_users(user_id, first_name, last_name, username)
        send_message_bot(user_id)

def get_first_name(message, last_name, username):
    first_name = message.text
    if not last_name:
        msg = bot.send_message(message.chat.id, 'Насабатонро дохил кунед')
        bot.register_next_step_handler(msg, get_last_name, first_name, username)
    elif not username:
        msg = bot.send_message(message.chat.id, 'User name-атонро дохил кунед')
        bot.register_next_step_handler(msg, get_username, first_name, last_name)
    else:
        add_users(message.chat.id, first_name, last_name, username)
        send_message_bot(message.chat.id)

def get_last_name(message, first_name, username):
    last_name = message.text
    if not username:
        msg = bot.send_message(message.chat.id, 'User name-атонро дохил кунед')
        bot.register_next_step_handler(msg, get_username, first_name, last_name)
    else:
        add_users(message.chat.id, first_name, last_name, username)
        send_message_bot(message.chat.id)

def get_username(message, first_name, last_name):
    username = message.text
    add_users(message.chat.id, first_name, last_name, username)
    send_message_bot(message.chat.id)

def send_message_bot(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton('Ман омадам')
    btn2 = types.KeyboardButton('Ман рафтам')
    btn3 = types.KeyboardButton('Ҷавоб мегирам')
    btn4 = types.KeyboardButton('Фикру андешаҳо нисбат ба бот')
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(user_id, "Бот кор карда истодааст.....", reply_markup=markup)

@bot.message_handler(commands=['help'])
def helping(message):
    bot.send_message(message.chat.id, f"""
    Ин бот барои ҳасту нест кардани студентоҳои SoftClub мебошад.
    
    1.Барои истифjда бурдани бот аз қисмати меню /start -
    ро пахш намоед то ки ботро истифода бурда тавонед.
    Пас аз пахш кардани /start агар ном ё насаб ё ин ки 
    номи корбаратон холи бошад пас аз шумо ҳамон набудаашро
    мепурсад шумо бошад онро дар чат нависед. Пасон дар поён 
    тугмаҳо пайдо мешаванд тугмаҳо инҳоянд "(Ман омадам, 
    Ман рафтам, Ҷавоб мегирам ва баҳо додан)".
    2.Бо пахш кардани тугмаи "Ман омадам" шуморо дар журнал
    қайд мекунад ки ба дарс омадед инчунини соати омадаатонро
    низ қайд мекунад.Агар шумо дар тули руз ин корро чанд бор
    такрор кунед ҳар бор аз шумо мепурсад вақти омадаатонро 
    иваз кардан мехоҳед ТУгмаи ҲА ва НЕ мебарояд ва яке аз 
    инро пахш кунед.
    3.Бо пахш кардани тугмаи "Ман рафтам" вақти рафтаи шумо
    сабт карда мешавад ва дуюм маротиба шумо ин корро анҷом
    дода наметавонед чун вақти рафтан як бор сабт мешавад.
    4.Бо пахши тугмаи "Ҷавоб мегирам" Аз шумо сабаби ҷавоб 
    пурсиданатонро мепурсад ва ҷавоби навистаатонро ба 
    устодатон равон мекунад ва устодатон ба шумо занг мезанад.
    5.Бо пахши тугмаи "Баҳо додан" ягон арзу шикоят бошад ё ин
    ки ягон чи гуфтани бтошед нависед!""")

@bot.message_handler()
def handler(message):
    if message.text == 'Ман омадам':
        add_arrival_time(message.chat.id,)
        
    elif message.text == 'Ман рафтам':
        add_time_to_go(message.chat.id)
    elif message.text == 'Ҷавоб мегирам':
        ask_for_absence_reason(message.chat.id)
    elif message.text == 'Фикру андешаҳо нисбат ба бот':
        ask_for_feedback(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Ин фармон нодуруст аст! Лутфан аз тугмаҳои зерин истифода баред.')

TEACHER_CHAT_ID = '-4229547290'
TEACHER_BOT_TOKEN = '7434629704:AAFAMfQaGF75MJtdr-z9Wc-4XS8WCAphZ18'

def ask_for_absence_reason(user_id):
    bot.send_message(user_id, "Ба дарс наомадан оқибатҳои бад дорад. Лутфан, сабаби ғоиб буданатонро нависед:")
    bot.register_next_step_handler_by_chat_id(user_id, process_absence_reason)

def process_absence_reason(message):
    user_id = message.chat.id
    reason = message.text
    
    bot.send_message(user_id, "Ман сабаби ғоиб буданатонро ба муаллиматон фиристодам. Онҳо каме дертар ба шумо менависанд.")
    send_reason_to_teachers(user_id, reason)

def send_reason_to_teachers(user_id, reason):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("SELECT FIRST_NAME, LAST_NAME FROM USERS WHERE USER_ID = %s", (str(user_id),))
        user_info = cur.fetchone()
        if user_info:
            first_name, last_name = user_info
            message_to_teachers = f"Хонанда {first_name} {last_name} (ID: {user_id}) сабаби ғоиб буданашро фиристод:\n\n{reason}"
            requests.get(f"https://api.telegram.org/bot{TEACHER_BOT_TOKEN}/sendMessage?chat_id={TEACHER_CHAT_ID}&text={message_to_teachers}")
        else:
            print(f"User information not found for user_id: {user_id}")
    except Exception as e:
        print(f"Error sending reason to teachers: {str(e)}")
    finally:
        close_connection(conn, cur)

bot.infinity_polling()