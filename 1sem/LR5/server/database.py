import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class GlossaryDatabase:
    def __init__(self, db_path="glossary.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert initial data
            self._seed_initial_data(conn)
            logger.info("Database initialized successfully")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _seed_initial_data(self, conn):
        """Seed database with initial Python terms"""
        initial_terms = [
            ('REST', '«передача репрезентативного состояния» или «передача „самоописываемого“ состояния») — архитектурный стиль взаимодействия компонентов распределённого приложения в сети.', 'web'),
            ('RPC', 'Удалённый вызов процедур (Remote Procedure Call, RPC) — это механизм, который позволяет одной программе вызывать процедуры или функции другой программы, расположенной на другом компьютере в сети.', 'web')
        ]

        for keyword, description, category in initial_terms:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO terms (keyword, description, category)
                    VALUES (?, ?, ?)
                ''', (keyword, description, category))
            except sqlite3.IntegrityError:
                pass

    def list_terms(self, skip=0, limit=100):
        """Get all terms with pagination"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT keyword, description, category, created_at 
                FROM terms 
                ORDER BY keyword 
                LIMIT ? OFFSET ?
            ''', (limit, skip))

            terms = [dict(row) for row in cursor.fetchall()]

            count_cursor = conn.execute('SELECT COUNT(*) FROM terms')
            total_count = count_cursor.fetchone()[0]

            return terms, total_count

    def get_term(self, keyword):
        """Get term by keyword"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT keyword, description, category, created_at 
                FROM terms WHERE keyword = ?
            ''', (keyword,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_term(self, keyword, description, category="general"):
        """Create a new term"""
        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO terms (keyword, description, category)
                    VALUES (?, ?, ?)
                ''', (keyword, description, category))
                return True
            except sqlite3.IntegrityError:
                return False

    def update_term(self, keyword, description=None, category=None):
        """Update an existing term"""
        with self.get_connection() as conn:
            update_fields = []
            params = []

            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            if category is not None:
                update_fields.append("category = ?")
                params.append(category)

            if not update_fields:
                return False

            params.append(keyword)
            query = f"UPDATE terms SET {', '.join(update_fields)} WHERE keyword = ?"

            cursor = conn.execute(query, params)
            return cursor.rowcount > 0

    def delete_term(self, keyword):
        """Delete a term"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM terms WHERE keyword = ?', (keyword,))
            return cursor.rowcount > 0