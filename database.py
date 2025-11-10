import sqlite3
from datetime import datetime

DB_FILE = "appointments.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS appointments
                      (id INTEGER PRIMARY KEY, contact TEXT, zip_code TEXT, time TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

init_db()  # Run on import

def save_appointment(contact, zip_code, time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO appointments (contact, zip_code, time, created_at) VALUES (?, ?, ?, ?)", 
                   (contact, zip_code, time, created_at))
    conn.commit()
    conn.close()

def is_after_hours():
    hour = datetime.now().hour
    return hour < 9 or hour >= 17  # Example: 9 AM - 5 PM