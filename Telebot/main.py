from telebot import TeleBot,types
import psycopg2

bot = TeleBot('7295059279:AAGreEW7Kzm2woOLl9ptbLbZLq5Wb5r88cs')

commands = [
    types.BotCommand('/start', 'Start bot'),
    
    types.BotCommand('/addtask','Add a task'),
    types.BotCommand('/gettasks','For delete task'),
    types.BotCommand('/deltask','Get all tasks'),
    types.BotCommand('/get','get'),
    types.BotCommand('/update_task','Update tasks'),
    types.BotCommand('/del','Delet user'),
   ]
bot.set_my_commands(commands)

def get_connection():
    connection = psycopg2.connect(
        database="telebot_db",
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
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS USERS
        (
            ID VARCHAR(100) PRIMARY KEY,
            FIRST_NAME VARCHAR(50) NULL,
            LAST_NAME VARCHAR(50) NULL,
            USER_NAME VARCHAR(100) NULL
        )
        """)
        conn.commit()
        return 'Table USERS created successfully'
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        close_connection(conn, cur)

def create_task_table():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS TASKS
        (
            ID SERIAL PRIMARY KEY,
            USER_ID VARCHAR(100) NOT NULL,
            TASK_NAME VARCHAR(100) NOT NULL,
            DUE_DATE VARCHAR(100) NULL,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            IS_COMPLETED BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (USER_ID) REFERENCES USERS(ID) ON DELETE CASCADE
        )
        """)
        conn.commit()
        return 'Table TASKS created successfully'
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        close_connection(conn, cur)

def add_user(id, first_name, last_name, user_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO USERS (ID, FIRST_NAME, LAST_NAME, USER_NAME)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ID) DO NOTHING
        """, (id, first_name, last_name, user_name))
        conn.commit()
        return f"User with id {id} created successfully"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['start'])
def started_bot(message):
    user_create = create_user_table()
    bot.send_message(message.chat.id, user_create)
    
    task_create = create_task_table()
    bot.send_message(message.chat.id, task_create)
    
    add_us = add_user(message.chat.id, message.chat.first_name, message.chat.last_name, message.chat.username)
    bot.send_message(message.chat.id, add_us)

@bot.message_handler(commands=['get'])
def get_users(message):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM USERS")
        users = cur.fetchall()
        if users:
            for user in users:
                bot.send_message(message.chat.id, f"ID: {user[0]}, First Name: {user[1]}, Last Name: {user[2]}, Username: {user[3]}")
        else:
            bot.send_message(message.chat.id, "No users found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['update'])
def update_user(message):
    try:
        command, first_name, last_name, user_name = message.text.split(maxsplit=3)
    except Exception as e:
        bot.send_message(message.chat.id, "Usage: /update <first_name> <last_name> <user_name>")
        return
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        UPDATE USERS SET FIRST_NAME = %s, LAST_NAME = %s, USER_NAME = %s WHERE ID = %s
        """, (first_name, last_name, user_name, str(message.chat.id)))
        conn.commit()
        bot.send_message(message.chat.id, f"User with id {message.chat.id} updated successfully")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['del'])
def delete_user(message):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM USERS WHERE ID = %s", (str(message.chat.id),))
        conn.commit()
        bot.send_message(message.chat.id, f'User with id {message.chat.id} deleted successfully')
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['addtask'])
def add_task(message):
    try:
        command, task_name, due_date = message.text.split(maxsplit=2)
    except Exception as e:
        bot.send_message(message.chat.id, "Usage: /addtask <task_name> <due_date>")
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO TASKS (USER_ID, TASK_NAME, DUE_DATE) 
        VALUES (%s, %s, %s)
        """, (str(message.chat.id), task_name, due_date))
        conn.commit()
        bot.send_message(message.chat.id, f"Task '{task_name}' added successfully with due date {due_date}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['gettask'])
def get_tasks(message):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM TASKS")
        tasks = cur.fetchall()
        if tasks:
            for task in tasks:
                bot.send_message(message.chat.id, f"ID: {task[0]}, Task name: {task[2]}, Due Date: {task[3]}, User ID: {task[1]}")
        else:
            bot.send_message(message.chat.id, "No tasks found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['deltask'])
def del_task(message):
    try:
        command, task_id = message.text.split(maxsplit=1)
    except Exception as e:
        bot.send_message(message.chat.id, "Usage: /deltask <task_id>")
        return
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM TASKS WHERE ID = %s", (task_id,))
        conn.commit()
        bot.send_message(message.chat.id, f'Task with id {task_id} deleted successfully')
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['update_task'])
def update_task(message):
    try:
        command, task_id, task_name, due_date = message.text.split(maxsplit=3)
        task_id = int(task_id)
    except Exception as e:
        bot.send_message(message.chat.id, "Usage: /update_task <task_id> <task_name> <due_date>")
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        UPDATE TASKS SET TASK_NAME = %s, DUE_DATE = %s WHERE ID = %s AND USER_ID = %s
        """, (task_name, due_date, task_id, str(message.chat.id)))
        conn.commit()
        bot.send_message(message.chat.id, f"Task with ID {task_id} updated successfully.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)

@bot.message_handler(commands=['complete_task'])
def complete_task(message):
    try:
        command, task_id = message.text.split(maxsplit=1)
        task_id = int(task_id)
    except Exception as e:
        bot.send_message(message.chat.id, "Usage: /complete_task <task_id>")
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE TASKS SET IS_COMPLETED = TRUE WHERE ID = %s AND USER_ID = %s", (task_id, str(message.chat.id)))
        conn.commit()
        bot.send_message(message.chat.id, f"Task with ID {task_id} marked as completed successfully.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    finally:
        close_connection(conn, cur)
    
@bot.message_handler(commands=['getalltasks'])
def get_all(messege):
    conn=get_connection()
    cur=conn.cursor()
    try:
        cur.execute("""select * from task""")
        for i in cur.fetchall():
            bot.send_message(messege.chat.id,f"""task name: {i[1]}\n created at: {i[3]}\n due date:{i[2]} """)
    except :
        return "Not found"
    finally:
        close_connection(conn,cur)

bot.infinity_polling()
