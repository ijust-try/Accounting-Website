import psycopg2
import psycopg2.extras
import os

# ── Load connection string from environment or config ──
try:
    from config import DATABASE_URL, ALLOWED_EMAILS
except ImportError:
    DATABASE_URL  = os.environ.get("DATABASE_URL", "")
    ALLOWED_EMAILS = []

def get_conn():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

def init_db():
    conn   = get_conn()
    cursor = conn.cursor()

    # ── allowed_users ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allowed_users (
            email TEXT PRIMARY KEY
        )
    """)

    # ── users ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       TEXT PRIMARY KEY,
            email         TEXT UNIQUE,
            password_hash TEXT
        )
    """)

    # ── customers ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            cid               SERIAL PRIMARY KEY,
            first_name        TEXT NOT NULL,
            last_name         TEXT,
            phone             TEXT UNIQUE NOT NULL,
            aadhar            TEXT,
            emergency_contact TEXT,
            gender            TEXT,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── stays ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stays (
            sid         SERIAL PRIMARY KEY,
            cid         INTEGER NOT NULL REFERENCES customers(cid),
            location    TEXT,
            room_number TEXT,
            checkin     DATE,
            checkout    DATE,
            status      TEXT DEFAULT 'active',
            rent_amount REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── payments ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id   SERIAL PRIMARY KEY,
            cid          INTEGER NOT NULL REFERENCES customers(cid),
            sid          INTEGER NOT NULL REFERENCES stays(sid),
            amount       REAL NOT NULL,
            payment_type TEXT DEFAULT 'rent',
            payment_date DATE,
            payment_mode TEXT DEFAULT 'cash',
            notes        TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── remarks ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remarks (
            rid        SERIAL PRIMARY KEY,
            cid        INTEGER NOT NULL REFERENCES customers(cid),
            note       TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── employees ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            eid         SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            phone       TEXT,
            aadhar      TEXT,
            address     TEXT,
            property    TEXT,
            base_salary REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── employee_payments ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_payments (
            epid       SERIAL PRIMARY KEY,
            eid        INTEGER NOT NULL REFERENCES employees(eid),
            amount     REAL NOT NULL,
            pay_type   TEXT DEFAULT 'salary',
            pay_date   DATE,
            notes      TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── employee_leaves ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_leaves (
            elid       SERIAL PRIMARY KEY,
            eid        INTEGER NOT NULL REFERENCES employees(eid),
            leave_date DATE NOT NULL,
            reason     TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── expenses ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            xid          SERIAL PRIMARY KEY,
            category     TEXT NOT NULL,
            sub_category TEXT,
            property     TEXT,
            amount       REAL NOT NULL,
            expense_date DATE,
            notes        TEXT,
            source_id    INTEGER DEFAULT NULL,
            source_type  TEXT DEFAULT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── insert allowed emails ──
    for email in ALLOWED_EMAILS:
        cursor.execute("""
            INSERT INTO allowed_users (email)
            VALUES (%s)
            ON CONFLICT (email) DO NOTHING
        """, (email.strip().lower(),))

    conn.commit()
    cursor.close()
    conn.close()
    print("DB initialized successfully.")

init_db()
