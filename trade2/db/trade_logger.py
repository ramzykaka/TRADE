import sqlite3

class TradeLogger:
    def __init__(self):
        self.conn = sqlite3.connect('trades.db', check_same_thread=False)
        self._create_table()

    def _create_table(self):
        """إنشاء جدول التداولات إذا لم يكن موجودًا"""
        self.conn.execute('''CREATE TABLE IF NOT EXISTS trades
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_id INTEGER NOT NULL,
                             symbol TEXT NOT NULL,
                             amount REAL NOT NULL,
                             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()

    def log_trade(self, user_id: int, symbol: str, amount: float):
        """تسجيل تداول جديد"""
        try:
            self.conn.execute(
                "INSERT INTO trades (user_id, symbol, amount) VALUES (?, ?, ?)",
                (user_id, symbol, amount)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging trade: {e}")

    def get_user_trades(self, user_id: int):
        """استرجاع تداولات مستخدم معين"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching trades: {e}")
            return []

    def __del__(self):
        """إغلاق الاتصال عند حذف الكائن"""
        self.conn.close()