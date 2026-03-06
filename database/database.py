import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('../.env')
PASSWORD = os.getenv("PASSWORD_DB")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")

conn = None

#подключение к бд
def connect_db():
    global conn
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=PASSWORD,
            port=3306
            #database="tasks_scheduler_db"
        )
        print("Подключение успешно!")
    except Exception as e:
        print("Подключение не удалось! Ошибка:", e)

#используем бд или создаем ее, если не создана
def init_db():
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS tasks_scheduler_db")
    cursor.execute("USE tasks_scheduler_db")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    tg_id INT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS format_outputs(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     format VARCHAR(100) NOT NULL);''')
    cursor.execute('''INSERT IGNORE INTO format_outputs(format)
                    VALUES 
                    ('Все задачи'), 
                    ('Задачи на неделю'), 
                    ('Задачи на сегодня');''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS timezones(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     utc INT NOT NULL);''')
    cursor.execute('''INSERT IGNORE INTO timezones(utc)
                    VALUES
                    (-1), (0), (1), (2), (3), (4),
                    (5), (6), (7), (8), (9);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sortings(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     format VARCHAR(100) NOT NULL);''')
    cursor.execute('''INSERT IGNORE INTO sortings(format)
                    VALUES
                    ('По порядку'), ('По названию'),
                    ('По дате');''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     notification INT NULL);''')
    cursor.execute('''INSERT IGNORE INTO notifications(notification)
                    VALUES
                    ('10'), ('30'),
                    ('60'), ('120');''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS weekdays(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     day VARCHAR(10) NULL);''')
    cursor.execute('''INSERT IGNORE INTO weekdays(day)
                    VALUES
                    ('Пн'), ('Вт'), ('Ср'), ('Чт'),
                    ('Пт'), ('Сб'), ('Вс');''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     user_id INT NOT NULL, 
                     timezone_id INT NOT NULL,
                     format_output_id INT NOT NULL, 
                     sorting_id INT NOT NULL,
                     FOREIGN KEY (user_id) REFERENCES users(id),
                     FOREIGN KEY (timezone_id) REFERENCES timezones(id),
                     FOREIGN KEY (format_output_id) REFERENCES format_outputs(id),
                     FOREIGN KEY (sorting_id) REFERENCES sortings(id));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks(
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     user_id INT NOT NULL, 
                     name VARCHAR(200) NOT NULL,
                     date DATE NOT NULL, 
                     time TIME NOT NULL,
                     notification_id INT NULL, 
                     is_status TINYINT NOT NULL,
                     FOREIGN KEY (user_id) REFERENCES users(id),
                     FOREIGN KEY (notification_id) REFERENCES notifications(id));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS periods (
                     id INT PRIMARY KEY AUTO_INCREMENT,
                     task_id INT NOT NULL,
                     weekday_id INT NOT NULL,
                     FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                     FOREIGN KEY (weekday_id) REFERENCES weekdays(id),
                     UNIQUE(task_id, weekday_id));''')
    conn.commit()
    cursor.close()


#--ДОБАВЛЕНИЕ--
#добавляем нового пользователя
def get_new_user(tg_id):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users(tg_id) VALUES (%s)', (tg_id,))
    conn.commit()
    cursor.close()

#выставляем дефолтные настройки
def set_default_settings(user_id, timezone):
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO settings(user_id, timezone_id, format_output_id, sorting_id)
                        VALUES (%s, %s, %s, %s)''', (user_id, timezone, 1, 1))
    conn.commit()
    cursor.close()

#сохранение задачи после добавления
def save_task(user_id, name, date, time, notification_id):
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tasks(user_id, name, date, time, notification_id, is_status)
                            VALUES (%s, %s, %s, %s, %s, %s)''', (user_id, name, date, time, notification_id, 0))
    conn.commit()
    cursor.close()

# сохранение периода задачи после добавления\изменение периода 2 (добавление новых записей)
def save_period_task(task_id, weekday_id):
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO periods(task_id, weekday_id)
                            VALUES (%s, %s)''', (task_id, weekday_id,))
    conn.commit()
    cursor.close()


#--ОБНОВЛЕНИЯ--
#выставляем первичный часовой пояс\изменение настроек (часовой пояс)
def update_timezone_settings(user_id, timezone):
    cursor = conn.cursor()
    cursor.execute('''UPDATE settings 
                    SET timezone_id = %s
                    WHERE user_id = %s ''', (timezone, user_id,))
    conn.commit()
    cursor.close()

#изменение настроек (формат вывода)
def update_format_output_settings(user_id, format_output_id):
    cursor = conn.cursor()
    cursor.execute('''UPDATE settings 
                    SET format_output_id = %s
                    WHERE user_id = %s ''', (format_output_id, user_id, ))
    conn.commit()
    cursor.close()

#изменение настроек (сортировка)
def update_sorting_settings(user_id, sorting_id):
    cursor = conn.cursor()
    cursor.execute('''UPDATE settings 
                    SET sorting_id = %s
                    WHERE user_id = %s ''', (sorting_id, user_id,))
    conn.commit()
    cursor.close()

#изменение имени
def edit_name_task(task_id, new_name):
    cursor = conn.cursor()
    cursor.execute('''UPDATE tasks 
                    SET name  = %s
                    WHERE id = %s''' , (new_name, task_id,))
    conn.commit()
    cursor.close()

#изменение даты
def edit_date_task(task_id, new_date):
    cursor = conn.cursor()
    cursor.execute('''UPDATE tasks 
                    SET date  = %s
                    WHERE id = %s''' , (new_date, task_id,))
    conn.commit()
    cursor.close()

#изменение времени
def edit_time_task(task_id, new_time):
    cursor = conn.cursor()
    cursor.execute('''UPDATE tasks 
                    SET time = %s
                    WHERE id = %s''' , (new_time, task_id,))
    conn.commit()
    cursor.close()

#изменение напоминания
def edit_notification_task(task_id, new_notification):
    cursor = conn.cursor()
    cursor.execute('''UPDATE tasks 
                    SET notification_id  = %s
                    WHERE id = %s''' , (new_notification, task_id,))
    conn.commit()
    cursor.close()

#--УДАЛЕНИЕ--


#изменение периода 1
def delete_old_period_task(task_id):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM periods 
                    WHERE task_id = %s''' , (task_id,))
    conn.commit()
    cursor.close()


#очищение всего списка задач пользователя 2
def clear_all_task_list(user_id):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM tasks 
                    WHERE user_id = %s''' , (user_id,))
    conn.commit()
    cursor.close()


#удаление задачи
def delete_task(user_id, task_id):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM tasks 
                    WHERE user_id = %s AND id = %s''',
                   (user_id, task_id,))
    conn.commit()
    cursor.close()

#--ВЫВОДЫ--

#выводим настройки
def output_settings(user_id):
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM settings WHERE user_id = %s''', (user_id,))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#выводим всех пользователей
def get_all_user():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#выводим все задачи определенного юзера (без напоминаний)
def get_all_tasks(user_id):
    # создаем курсор, который передвигается по бд
    cursor = conn.cursor()
    #выполняем запрос
    cursor.execute("SELECT name, date, time, is_status FROM tasks WHERE user_id = %s", (user_id, ))
    #распаковали курсор, вытащили записи и получили список кортежей
    rows = cursor.fetchall()
    #выводим каждую запись
    for row in rows:
        print(row)
    #курсор закрываем
    cursor.close()

# выводим все задачи определенного юзера (с напоминаниями)
def get_all_tasks_notification(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, date, time, notification_id, is_status FROM tasks WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#выводим период задачи (но если нужны все задачи одного юзера, то нужно вывести по юзер_айди?
def output_period_task(task_id):
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM periods WHERE task_id = %s''', (task_id,))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#выводим все задачи определенного юзера на неделю(с пн по настоящий день)
def get_all_tasks_weekday(user_id, current_date):
    cursor = conn.cursor()
    cursor.execute("SELECT name, date, time, is_status FROM tasks WHERE user_id = %s AND date >= %s", (user_id, current_date, ))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#выводим все задачи определенного юзера на сегодня
def get_all_tasks_today(user_id, current_date):
    cursor = conn.cursor()
    cursor.execute("SELECT name, date, time, is_status FROM tasks WHERE user_id = %s AND date = %s", (user_id, current_date, ))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()

#для отладки, потом удалить
def get_all_tasks_debugging():
    # создаем курсор, который передвигается по бд
    cursor = conn.cursor()
    #выполняем запрос
    cursor.execute("SELECT * FROM tasks")
    #распаковали курсор, вытащили записи и получили список кортежей
    rows = cursor.fetchall()
    #выводим каждую запись
    for row in rows:
        print(row)
    #курсор закрываем
    cursor.close()

#отключаемся от бд
def close_conn():
    conn.close()


#тесты
connect_db()
init_db()
#get_new_user(1255424)
#set_default_settings(3, 2)
#update_timezone_settings(2, 3)
#output_settings(3)
#get_all_user()
#edit_time_task(1, '14:00:00')
#save_task(2, 'Задача тестовая3', '2026-03-05', '12:00:00', 1)
#save_period_task(2, 5)
#save_period_task(3, 4)
#output_period_task(4)
#edit_notification_task(1, 2)
#edit_date_task(1, '2026-03-01')
#edit_name_task(1, "Задачка")
#delete_old_period_task(1)
#save_period_task(1, 5)
#clear_all_task_list_periods(3)
#clear_all_task_list_periods(2)
#clear_all_task_list(2)
#delete_task(1, 1)
#delete_task_periods(4)
#output_period_task(2)
#output_period_task(3)
#get_all_tasks(2)
#get_all_tasks_notification(2)
#get_all_tasks_weekday(2, '2026-03-02')
#get_all_tasks_today(2, '2026-03-05')
#update_format_output_settings(3, 2)
#update_sorting_settings(3, 2)
get_all_tasks_debugging()
close_conn()