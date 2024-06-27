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

