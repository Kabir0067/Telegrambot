from telebot.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, time
from telebot import TeleBot, types
import psycopg2
import requests


TEACHER_CHAT_ID = '-4130244659'
TEACHER_BOT_TOKEN = '7434629704:AAFAMfQaGF75MJtdr-z9Wc-4XS8WCAphZ18'

bot = TeleBot('7209349514:AAGXBHcIOJRNhKrWmm8eErdBiR5BhADw8kg')

commands = [
    types.BotCommand('/start', 'Барои оғоз кардани кор бо бот'),
    types.BotCommand('/help', 'Кумакрасони ва тарзи истифодаи бот')
]
bot.set_my_commands(commands)

def connection_database():
    connection = psycopg2.connect(
        database="hastunests_db",
        user="postgres",
        host="localhost",
        password="1234",
        port=5432
    )
    return connection

def close_connection(conn, cur):
    cur.close()
    conn.close()

def create_table_users():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS USERS(
                USER_ID VARCHAR(150) PRIMARY KEY,
                FIRST_NAME VARCHAR(50) NOT NULL,
                LAST_NAME VARCHAR(50) NOT NULL,
                USERNAME VARCHAR(100) NOT NULL,
                GROUP_NAME VARCHAR(50) NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def add_user_in_table(user_id, first_name, last_name, username, group_name):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO USERS(USER_ID, FIRST_NAME, LAST_NAME, USERNAME, GROUP_NAME)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (USER_ID) DO NOTHING
            """, (str(user_id), first_name, last_name, username, group_name))
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def create_table_came_and_went():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS COME_AND_WENT(
                CW_ID SERIAL PRIMARY KEY,
                USER_ID VARCHAR(150),
                TIME_TO_COME TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                TIME_TO_GO TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                DATE DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (USER_ID) REFERENCES USERS(USER_ID)
            )
        """)
        conn.commit()
        print("COME_AND_WENT table created successfully")
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def check_time_to_come(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        today = date.today()
        cur.execute("""
            SELECT TIME_TO_COME FROM COME_AND_WENT
            WHERE USER_ID = %s AND DATE = %s
        """, (str(user_id), today))
        result = cur.fetchone()
        return result
    except Exception as e: 
        print(f'Error: {str(e)}')
        return None
    finally:
        close_connection(conn, cur)

def add_time_to_come(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        existing_time = check_time_to_come(user_id)
        if existing_time:
            bot.send_message(user_id, f'Вақти омадани шумо илова карда шуда буд:  Мехоҳед таъғир диҳед?')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn_ha = types.KeyboardButton('Ҳа')
            btn_ne = types.KeyboardButton('Не')
            markup.add(btn_ha, btn_ne)
            bot.send_message(user_id, 'Тасдиқ кунед Ҳа ё Не:', reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(user_id, update_arrival)
        else:
            now = datetime.now()
            time_to_come = now.strftime('%Y-%m-%d %H:%M')
            cur.execute("""
                INSERT INTO COME_AND_WENT(USER_ID,TIME_TO_COME,DATE) VALUES
                (%s,%s,%s)""", (str(user_id), time_to_come, now.date())) 
            conn.commit()
            bot.send_message(user_id, f'Вақти омадан шумо илова карда шуд: {time_to_come}') 
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def update_arrival(message): 
    user_id = message.chat.id
    if message.text == 'Ҳа':
        time_to_come = datetime.now().strftime('%Y-%m-%d %H:%M')
        conn = connection_database()
        cur = conn.cursor()
        try:    
            cur.execute("""
                UPDATE COME_AND_WENT SET TIME_TO_COME = %s WHERE USER_ID = %s AND DATE = %s
            """, (time_to_come, str(user_id), date.today()))
            conn.commit()
            bot.send_message(user_id, f'Вақти омадани шумо иваз карда шуд: {time_to_come}') 
            send_message_bot(message.chat.id)
        except Exception as e:
            print(f'Error: {str(e)}')
        finally:
            close_connection(conn, cur)
    elif message.text == 'Не':
        bot.send_message(user_id, 'Ташаккур! Мо вақтатонро иваз намекунем.')
        send_message_bot(message.chat.id)

def check_time_to_go(user_id):
    conn = connection_database()
    cur = conn.cursor()
    try:
        today = date.today()
        cur.execute("""
            SELECT TIME_TO_GO FROM COME_AND_WENT
            WHERE USER_ID = %s AND DATE = %s
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
        bot.send_message(user_id, f'Шумо метавонед вақти рафтанро танҳо як маротиба дар як рӯз ворид кунед.')
    else:
        try:
            conn = connection_database()
            cur = conn.cursor()
            time_to_go = datetime.now()
            cur.execute("""
               INSERT INTO COME_AND_WENT (USER_ID, TIME_TO_GO, DATE)
               VALUES (%s, %s, %s)
              """, (str(user_id), time_to_go, time_to_go.date()))
            conn.commit()
            bot.send_message(user_id, f'Вақти рафтани шумо сабт шуд: {time_to_go}')
        except Exception as e:
            print(f'Error adding departure time: {str(e)}')
        finally:
            close_connection(conn, cur)


def ask_for_absence_reason(user_id):
    bot.send_message(user_id, "Ба дарс наомадан оқибатҳои нохуб дорад. Лутфан, сабаби наомаданатонро гӯед.")
    bot.register_next_step_handler_by_chat_id(user_id, process_absence_reason)

def process_absence_reason(message):
    user_id = message.chat.id
    reason = message.text
    bot.send_message(user_id, "Ман сабаби наомаданатонро ба муаллиматон фиристодам. Онкас каме дертар ба шумо ҷавоб хоҳанд дод.")
    send_reason_to_teachers(user_id, reason)

def send_reason_to_teachers(user_id, reason):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("SELECT FIRST_NAME, LAST_NAME, USERNAME, GROUP_NAME FROM USERS WHERE USER_ID = %s", (str(user_id),))
        user_info = cur.fetchone()
        if user_info:
            first_name, last_name, username, group_name = user_info
            message_to_teachers = f"""
Донишҷӯ --> {first_name} {last_name}
Аз гурӯҳи --> {group_name}
Телеграм акаунт --> @{username}

Сабаби наомаданаш:
{reason}

"""
            requests.get(f"https://api.telegram.org/bot{TEACHER_BOT_TOKEN}/sendMessage?chat_id={TEACHER_CHAT_ID}&text={message_to_teachers}&parse_mode=Markdown")
        else:
            print(f"User information not found for user_id: {user_id}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)


def ask_the_reason_for_the_delay(user_id):
    bot.send_message(user_id, 'Сабаби деркарданатонро мегуфтед? 🤨')
    bot.register_next_step_handler_by_chat_id(user_id, the_reason_for_being_late)

def the_reason_for_being_late(message):
    user_id = message.chat.id
    reason = message.text
    bot.send_message(user_id, "Ман сабаби дер карданатонро ба муаллиматон фиристодам. Онкас шахсан бо шумо суҳбат мекунанд!! 😑")
    reason_to_teachers(user_id, reason)

def reason_to_teachers(user_id, reason):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("SELECT FIRST_NAME, LAST_NAME, USERNAME, GROUP_NAME FROM USERS WHERE USER_ID = %s", (str(user_id),))
        user_info = cur.fetchone()
        if user_info:
            first_name, last_name, username, group_name = user_info
            message_to_teachers = f"""
Донишҷӯ --> {first_name.upper()} {last_name.upper()}
Аз гурӯҳи --> {group_name.upper()}
Телеграм акаунт --> @{username}

Сабаби дер карданаш:
{reason}

"""
            requests.post(f"https://api.telegram.org/bot{TEACHER_BOT_TOKEN}/sendMessage?chat_id={TEACHER_CHAT_ID}&text={message_to_teachers}&parse_mode=Markdown")
        else:
            print(f"User information not found for user_id: {user_id}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)


def create_table_feedbacks():
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE FEEDBACK(
                FDB_ID SERIAL PRIMARY KEY,
                FEEDBACK_TEXT TEXT,
                SUBMISSION_TIME DATE DEFAULT CURRENT_DATE,
                USER_ID VARCHAR(150),
                FOREIGN KEY (USER_ID) REFERENCES USERS(USER_ID)
            )""")
        conn.commit()
    except Exception as e:
        print(f'Eror {e}')
    finally:
        close_connection(conn, cur)

def add_feedback(user_id, feedback_text):
    conn = connection_database()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO FEEDBACK (user_id, FEEDBACK_TEXT) VALUES (%s, %s)
        """, (str(user_id), feedback_text))
        conn.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        close_connection(conn, cur)

def ask_for_feedback(user_id):
    msg = bot.send_message(user_id, "Лутфан, Фикру андешаатонро нисбат ба барнома нависед 😊:")
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    user_id = message.chat.id
    feedback_text = message.text
    add_feedback(user_id, feedback_text)
    bot.send_message(user_id, "Ташаккур барои Фикру андешаҳо нисбат ба барнома 🙏!")
    send_message_bot(user_id)

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

@bot.message_handler(commands=['start'])
def start(message):
    create_table_users()
    create_table_came_and_went()
    create_table_feedbacks()
    
    user_id = message.chat.id
    first_name = message.chat.first_name or ''
    last_name = message.chat.last_name or ''
    username = message.chat.username or ''
    group_name = ''
    if not first_name:
        msg = bot.send_message(user_id, 'Наматонро дохил кунед 😊')
        bot.register_next_step_handler(msg, get_first_name, last_name, username, group_name)
    elif not last_name:
        msg = bot.send_message(user_id, 'Насабатонро дохил кунед 😊')
        bot.register_next_step_handler(msg, get_last_name, first_name, username, group_name)
    elif not username:
        msg = bot.send_message(user_id, 'Telegram акаунти худро дохил кунед 😊')
        bot.register_next_step_handler(msg, get_username, first_name, last_name, group_name)
    else:
        get_group_name(message, first_name, last_name, username)

def get_first_name(message, last_name, username, group_name):
    first_name = message.text
    msg = bot.send_message(message.chat.id, 'Насабатонро дохил кунед 😊')
    bot.register_next_step_handler(msg, get_last_name, first_name, username, group_name)

def get_last_name(message, first_name, username, group_name):
    last_name = message.text
    msg = bot.send_message(message.chat.id, 'Telegram акаунти худро дохил кунед 😊')
    bot.register_next_step_handler(msg, get_username, first_name, last_name, group_name)

def get_username(message, first_name, last_name, group_name):
    username = message.text
    get_group_name(message, first_name, last_name, username)

def get_group_name(message, first_name, last_name, username):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btns = ['Cpp', 'HTML & CSS', 'Dart', 'Python', 'C Sharp','.NET', 'J.Script', 'J.Script 2', 'React', 'React 2', 'UХ/UI', 'Cpp Olimpiad', 'Дигар']
    buttons = [KeyboardButton(btn) for btn in btns]
    markup.add(*buttons)
    msg = bot.send_message(message.chat.id, 'Номи гурӯҳатонро аз инҷо интихоб кунед ё ки ворид кунед 😊', reply_markup=markup)
    bot.register_next_step_handler(msg, process_group_choice, first_name, last_name, username)

def process_group_choice(message, first_name, last_name, username):
    group_name = message.text
    if group_name == 'Дигар':
        msg = bot.send_message(message.chat.id, 'Номи гурӯҳатонро дохил кунед 😊')
        bot.register_next_step_handler(msg, process_custom_group_name, first_name, last_name, username)
    else:
        add_user_in_table(message.chat.id, first_name, last_name, username, group_name)
        send_message_bot(message.chat.id)

def process_custom_group_name(message, first_name, last_name, username):
    group_name = message.text
    add_user_in_table(message.chat.id, first_name, last_name, username, group_name)
    send_message_bot(message.chat.id)

def send_message_bot(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton('Ман омадам')
    btn2 = types.KeyboardButton('Ман рафтам')
    btn3 = types.KeyboardButton('Дер мекунам')
    btn4 = types.KeyboardButton('Ҷавоб мегирам')
    btn5 = types.KeyboardButton('Фикру андешаҳо нисбат ба барнома')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(user_id, 'Якеро интихоб кунед.', reply_markup=markup)


@bot.message_handler()
def handler(message):
    if message.text == 'Ман омадам':
        add_time_to_come(message.chat.id)
        pass
    elif message.text == 'Ман рафтам':
        add_time_to_go(message.chat.id)
        
    elif message.text == 'Ҷавоб мегирам':
        ask_for_absence_reason(message.chat.id)
        
    elif message.text == 'Дер мекунам':
        ask_the_reason_for_the_delay(message.chat.id)

    elif message.text == 'Фикру андешаҳо нисбат ба барнома':
        ask_for_feedback(message.chat.id)  
    else:
        bot.send_message(message.chat.id, 'Ин фармон нодуруст аст! Лутфан аз тугмаҳои зерин истифода баред.')


bot.polling(none_stop=True)