import sqlite3
import datetime
from src.modules.base.base_module.base_module import BaseModule

class SqliteModule(BaseModule):

    ready_for_interface = True
    accepts_any_input = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect('./data.db')
        cursor = connection.cursor()
        # Создаем таблицу Users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
        signature TEXT,
        time TEXT,
        message TEXT
        )
        ''')
        connection.commit()
        connection.close()


    def process_message(self, signature, message):
        connection = sqlite3.connect('./data.db')
        cursor = connection.cursor()
        cursor.execute(f'INSERT INTO messages (signature, time, message) VALUES (?, ?, ?)',
                       (signature, str(datetime.datetime.now().strftime('%X')), str(message)))

        connection.commit()
        connection.close()
