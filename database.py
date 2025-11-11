import sqlite3
import logging
from contextlib import contextmanager

class Database:
    def __init__(self, db_path='bot_database.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    task_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            logging.error(f'Ошибка базы данных: {e}')
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_task(self, user_id, task_text):
        """Добавить задачу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tasks (user_id, task_text) VALUES (?, ?)',
                (user_id, task_text)
            )
            conn.commit()
            return cursor.lastrowid

    def get_user_tasks(self, user_id):
        """Получение задач пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, task_text FROM tasks WHERE user_id = ? ORDER BY created_at',
                (user_id,)
            )
            return cursor.fetchall()

    def delete_task(self, user_id, task_id):
        """Удаление задачи"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM tasks WHERE id = ? AND user_id = ?',
                (task_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0