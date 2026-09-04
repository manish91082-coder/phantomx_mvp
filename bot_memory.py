import sqlite3
import json
from typing import Dict, Any

class ProjectMemory:
    def __init__(self, db_path='phantomx_memory.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS memory_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS dry_run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                chain TEXT,
                pair TEXT,
                expected_profit_usd REAL,
                status TEXT,
                tx_data TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def set_state(self, key: str, value: Any):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('REPLACE INTO memory_state (key, value) VALUES (?, ?)', (key, json.dumps(value)))
        conn.commit()
        conn.close()

    def get_state(self, key: str) -> Any:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT value FROM memory_state WHERE key = ?', (key,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None

    def log_dry_run(self, chain: str, pair: str, profit: float, status: str, tx_data: dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO dry_run_logs (chain, pair, expected_profit_usd, status, tx_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (chain, pair, profit, status, json.dumps(tx_data)))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    mem = ProjectMemory()
    mem.set_state('last_scanned_block', 1000)
    print(f"Memory Continuity Check: {mem.get_state('last_scanned_block')}")
