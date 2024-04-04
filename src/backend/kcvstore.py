import sqlite3

class KCVStore:
    def __init__(self, dbpath):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kcvstore (
                key TEXT PRIMARY KEY,
                category TEXT,
                value TEXT
            )
        ''')
        self.conn.commit()

    def set(self, key, category, value):
        self.cursor.execute('''
            INSERT OR REPLACE INTO kcvstore (key, category, value)
            VALUES (?, ?, ?)
        ''', (key, category,value))
        self.conn.commit()

    def get(self, key, category):
        self.cursor.execute('''
            SELECT value FROM kcvstore WHERE key = ? and category = ?
        ''', (key,category))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def delete(self, key,category):
        self.cursor.execute('''
            DELETE FROM kcvstore WHERE key = ? and category = ?
        ''', (key,category))
        self.conn.commit()

    def close(self):
        self.conn.close()