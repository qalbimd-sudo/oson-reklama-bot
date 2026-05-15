import sqlite3

def init_db():
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            phone_number TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_type TEXT,
            dimensions TEXT,
            material TEXT,
            design_status TEXT,
            installation_location TEXT,
            deadline TEXT,
            status TEXT,
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

def add_user(telegram_id, name, phone_number):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (telegram_id, name, phone_number) VALUES (?, ?, ?)", (telegram_id, name, phone_number))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_order(user_id, service_type, dimensions, material, design_status, installation_location, deadline, status):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, service_type, dimensions, material, design_status, installation_location, deadline, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (user_id, service_type, dimensions, material, design_status, installation_location, deadline, status))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status):
    conn = sqlite3.connect("oson_reklama.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

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
    return history[::-1] # Return in chronological order
