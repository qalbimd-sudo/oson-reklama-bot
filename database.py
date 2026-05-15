import sqlite3

def init_db():
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            phone_number TEXT,
            language TEXT DEFAULT 'uz'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_type TEXT,
            dimensions TEXT,
            location_lat REAL,
            location_lon REAL,
            voice_file_id TEXT,
            description TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_user(telegram_id, name, phone_number, language='uz'):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (telegram_id, name, phone_number, language) VALUES (?, ?, ?, ?)", (telegram_id, name, phone_number, language))
    conn.commit()
    conn.close()

def update_user_language(telegram_id, language):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_order(user_id, service_type, dimensions, location_lat=None, location_lon=None, voice_file_id=None, description=None, status='Kutilmoqda'):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (user_id, service_type, dimensions, location_lat, location_lon, voice_file_id, description, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, service_type, dimensions, location_lat, location_lon, voice_file_id, description, status))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def add_chat_message(user_id, role, content):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(user_id, limit=10):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return history[::-1]
