import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('../.env')
PASSWORD = os.getenv("PASSWORD_DB")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")


class Database:
    def __init__(self, db_host, db_user, password, port):
        self.__conn = None
        self.connect_db(db_host, db_user, password, port)
        self.init_db()

    def connect_db(self, db_host, db_user, password, port):
        try:
            self.__conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=password,
                port=port)
            print("Подключение успешно!")
        except Exception as e:
            print("Подключение не удалось! Ошибка:", e)

    def init_db(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS tasks_scheduler_db")
            cursor.execute("USE tasks_scheduler_db")
            #cursor.execute("DROP TABLE IF EXISTS periods, tasks, settings, users, format_outputs, timezones, sortings, notifications, weekdays;")
            cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            tg_id INT NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS format_outputs(
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             format VARCHAR(100) NOT NULL UNIQUE);''')
            cursor.execute('''INSERT IGNORE INTO format_outputs(format)
                            VALUES 
                            ('Все задачи'), 
                            ('Задачи на неделю'), 
                            ('Задачи на сегодня');''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS timezones(
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             utc INT NOT NULL UNIQUE);''')
            cursor.execute('''INSERT IGNORE INTO timezones(utc)
                            VALUES
                            (-1), (0), (1), (2), (3), (4),
                            (5), (6), (7), (8), (9);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS sortings(
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             format VARCHAR(100) NOT NULL UNIQUE);''')
            cursor.execute('''INSERT IGNORE INTO sortings(format)
                            VALUES
                            ('По порядку'), ('По названию'),
                            ('По дате');''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS notifications(
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             notification INT NULL UNIQUE);''')
            cursor.execute('''INSERT IGNORE INTO notifications(notification)
                            VALUES (0),
                            (10), (30),
                            (60), (120);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS weekdays(
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             day VARCHAR(10) NULL UNIQUE);''')
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
                             is_status TINYINT DEFAULT NULL,
                             FOREIGN KEY (user_id) REFERENCES users(id),
                             FOREIGN KEY (notification_id) REFERENCES notifications(id));''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS periods (
                             id INT PRIMARY KEY AUTO_INCREMENT,
                             task_id INT NOT NULL,
                             weekday_id INT NOT NULL,
                             FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                             FOREIGN KEY (weekday_id) REFERENCES weekdays(id),
                             UNIQUE(task_id, weekday_id));''')
        self.__conn.commit()

    # --ПРОВЕРКА--
    # есть ли юзер в системе
    def is_exist_user(self, tg_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE tg_id = %s", (tg_id,))
            rows = cursor.fetchall()
            return bool(rows)


    # --ДОБАВЛЕНИЕ--
    # добавляем нового пользователя
    def add_new_user(self, tg_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT INTO users(tg_id) VALUES (%s)", (tg_id,))
        self.__conn.commit()

    # выставляем дефолтные настройки
    def set_default_settings(self, user_id, timezone):
        with self.__conn.cursor() as cursor:
            cursor.execute('''INSERT INTO settings(user_id, timezone_id, format_output_id, sorting_id)
                            VALUES (%s, %s, %s, %s)''', (user_id, timezone, 1, 1))
        self.__conn.commit()

    # сохранение задачи после добавления
    def save_task(self, user_id, name, date, time, notification_id, is_status=None):
        with self.__conn.cursor() as cursor:
            cursor.execute('''INSERT INTO tasks(user_id, name, date, time, notification_id, is_status)
                                VALUES (%s, %s, %s, %s, %s, %s)''', (user_id, name, date, time, notification_id, is_status))
            new_id = cursor.lastrowid #получаем айди добавленной только что задачи
        self.__conn.commit()
        return new_id

    # сохранение периода задачи после добавления\изменение периода 2 (добавление новых записей)
    def save_period_task(self, task_id, weekday_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''INSERT INTO periods(task_id, weekday_id)
                                VALUES (%s, %s)''', (task_id, weekday_id,))
        self.__conn.commit()


    # --ОБНОВЛЕНИЯ--
    # выставляем первичный часовой пояс\изменение настроек (часовой пояс)
    def update_timezone_settings(self, user_id, timezone):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE settings 
                        SET timezone_id = %s
                        WHERE user_id = %s ''', (timezone, user_id,))
        self.__conn.commit()

    # изменение настроек (формат вывода)
    def update_format_output_settings(self, user_id, format_output_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE settings 
                        SET format_output_id = %s
                        WHERE user_id = %s ''', (format_output_id, user_id,))
        self.__conn.commit()

    # изменение настроек (сортировка)
    def update_sorting_settings(self, user_id, sorting_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE settings 
                        SET sorting_id = %s
                        WHERE user_id = %s ''', (sorting_id, user_id,))
        self.__conn.commit()

    # изменение имени
    def edit_name_task(self, task_id, new_name):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tasks 
                        SET name  = %s
                        WHERE id = %s''', (new_name, task_id,))
        self.__conn.commit()

    # изменение даты
    def edit_date_task(self, task_id, new_date):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tasks 
                        SET date  = %s
                        WHERE id = %s''', (new_date, task_id,))
        self.__conn.commit()

    # изменение времени
    def edit_time_task(self, task_id, new_time):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tasks 
                        SET time = %s
                        WHERE id = %s''', (new_time, task_id,))
        self.__conn.commit()

    # изменение напоминания
    def edit_notification_task(self, task_id, new_notification):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tasks 
                        SET notification_id  = %s
                        WHERE id = %s''', (new_notification, task_id,))
        self.__conn.commit()

    # изменение статуса выполнения
    def edit_is_status_task(self, task_id, new_status):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tasks 
                           SET is_status = %s
                           WHERE id = %s''', (new_status, task_id,))
        self.__conn.commit()

    # --УДАЛЕНИЕ--
    # изменение периода 1
    def delete_old_period_task(self, task_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM periods 
                        WHERE task_id = %s''', (task_id,))
        self.__conn.commit()

    # очищение всего списка задач пользователя 2
    def clear_all_task_list(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM tasks 
                        WHERE user_id = %s''', (user_id,))
        self.__conn.commit()

    # удаление задачи
    def delete_task(self, user_id, task_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM tasks 
                        WHERE user_id = %s AND id = %s''',
                       (user_id, task_id,))
        self.__conn.commit()


    # --ВЫВОДЫ--
    #получаем айди юзера
    def get_user_id(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE tg_id = %s", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем айди часового пояса
    def get_timezone_id(self, utc):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM timezones WHERE utc = %s", (utc,))
            row = cursor.fetchone()
            return row[0] if row else None

    #по айди получаем значение часового пояса
    def get_timezone(self, timezone_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT utc FROM timezones WHERE id = %s", (timezone_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем айди формата вывода
    def get_format_outputs_id(self, format_output):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM format_outputs WHERE format = %s", (format_output,))
            row = cursor.fetchone()
            return row[0] if row else None

    # по айди получаем значение формата вывода
    def get_format_outputs(self, format_output_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT format FROM format_outputs WHERE id = %s", (format_output_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем айди сортировки
    def get_sorting_id(self, format_sorting):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM sortings WHERE format = %s", (format_sorting,))
            row = cursor.fetchone()
            return row[0] if row else None

    # по айди получаем значение сортировки
    def get_sorting(self, format_sorting_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT format FROM sortings WHERE id = %s", (format_sorting_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем айди напоминания
    def get_notification_id(self, notification):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM notifications WHERE notification = %s", (notification,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем айди дня недели
    def get_weekday_id(self, day):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM weekdays WHERE day = %s", (day,))
            row = cursor.fetchone()
            return row[0] if row else None

    # получаем день недели по айди
    def get_weekday(self, day_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT day FROM weekdays WHERE id = %s", (day_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # выводим настройки
    def output_settings(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM settings WHERE user_id = %s", (user_id,))
            return cursor.fetchone()

    # выводим всех пользователей (возвращаем список всех строк)
    def get_all_user(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()

    # выводим все задачи определенного юзера
    def get_all_tasks(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id, name, date, time, notification_id, is_status FROM tasks WHERE user_id = %s", (user_id,))
            return cursor.fetchall()

    # выводим период задачи
    def output_period_task(self, task_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM periods WHERE task_id = %s", (task_id,))
            rows = cursor.fetchall()
            return [row[2] for row in rows]

    # выводим все задачи определенного юзера на неделю(с пн по настоящий день)
    def get_all_tasks_weekday(self, user_id, current_date):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT name, date, time, is_status FROM tasks WHERE user_id = %s AND date >= %s",
                           (user_id, current_date,))
            return cursor.fetchall()

    # выводим все задачи определенного юзера на сегодня
    def get_all_tasks_today(self, user_id, current_date):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT name, date, time, is_status FROM tasks WHERE user_id = %s AND date = %s",
                           (user_id, current_date,))
            return cursor.fetchall()



    # для отладки, потом удалить
    def get_all_tasks_debugging(self):
        # создаем курсор, который передвигается по бд
        cursor = self.__conn.cursor()
        # выполняем запрос
        cursor.execute("SELECT * FROM tasks")
        # распаковали курсор, вытащили записи и получили список кортежей
        rows = cursor.fetchall()
        # выводим каждую запись
        for row in rows:
            print(row)
        # курсор закрываем
        cursor.close()

    # отключаемся от бд
    def close_conn(self):
        self.__conn.close()

database = Database(DB_HOST, DB_USER, PASSWORD,3306)

#тесты

#database.get_new_user(1255424)
#database.set_default_settings(3, 2)
#database.update_timezone_settings(2, 3)
#database.output_settings(3)
#database.get_all_user()
#database.edit_time_task(1, '14:00:00')
#database.save_task(2, 'Задача тестовая3', '2026-03-05', '12:00:00', 1)
#database.save_period_task(2, 5)
#database.save_period_task(3, 4)
#database.output_period_task(4)
#database.edit_notification_task(1, 2)
#database.edit_date_task(1, '2026-03-01')
#database.edit_name_task(1, "Задачка")
#database.delete_old_period_task(1)
#database.save_period_task(1, 5)
#database.clear_all_task_list_periods(3)
#database.clear_all_task_list_periods(2)
#database.clear_all_task_list(2)
#database.delete_task(1, 1)
#database.delete_task_periods(4)
#database.output_period_task(2)
#database.output_period_task(3)
#database.get_all_tasks(2)
#database.get_all_tasks_notification(2)
#database.get_all_tasks_weekday(2, '2026-03-02')
#database.get_all_tasks_today(2, '2026-03-05')
#database.update_format_output_settings(3, 2)
#database.update_sorting_settings(3, 2)
database.get_all_tasks_debugging()
#database.close_conn()