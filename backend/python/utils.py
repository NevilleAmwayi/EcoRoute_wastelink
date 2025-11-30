# utils.py
import sqlite3
import json
from datetime import datetime
import os

# -------------------------
# DATABASE PATH
# -------------------------
DB_NAME = os.path.join(os.path.dirname(__file__), "wastelink.db")

# -------------------------
# TABLE NAME CONSTANTS
# -------------------------
USERS = "users"
PICKUP_REQUESTS = "pickup_requests"
COLLECTIONS = "collections"
NOTIFICATIONS = "notifications"
EARNINGS = "earnings"
WASTE_PRICING = "waste_pricing"
DAILY_METRICS = "daily_metrics"
TRANSACTIONS = "transactions"
AUDIT_LOGS = "audit_logs"
LOCATIONS = "locations"
RECYCLING_CENTERS = "recycling_centers"
WASTE_REPORTS = "waste_reports"
ROUTES = "routes"
FEEDBACK = "feedback"
PAYMENTS = "payments"

# -------------------------
# CONNECT TO DB
# -------------------------
def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# INITIALIZE DATABASE
# -------------------------
def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.executescript(f"""
    -- USERS
    CREATE TABLE IF NOT EXISTS {USERS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('resident','collector','admin')) NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        profile_image TEXT,
        collector_latitude REAL,
        collector_longitude REAL,
        collector_address TEXT,
        is_available INTEGER DEFAULT 1,
        total_earnings REAL DEFAULT 0.00,
        completed_pickups INTEGER DEFAULT 0,
        rating REAL DEFAULT 0.00,
        vehicle_type TEXT,
        capacity_kg REAL,
        status TEXT CHECK(status IN ('active','inactive','pending')) DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- PICKUP REQUESTS
    CREATE TABLE IF NOT EXISTS {PICKUP_REQUESTS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        resident_id TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        location_notes TEXT,
        status TEXT CHECK(status IN ('pending','assigned','arrived','completed','cancelled')) DEFAULT 'pending',
        assigned_collector_id TEXT,
        assigned_at TEXT,
        requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY(resident_id) REFERENCES {USERS}(id),
        FOREIGN KEY(assigned_collector_id) REFERENCES {USERS}(id)
    );

    -- COLLECTIONS
    CREATE TABLE IF NOT EXISTS {COLLECTIONS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        request_id TEXT NOT NULL,
        collector_id TEXT NOT NULL,
        waste_photo_url TEXT,
        ai_classification_data TEXT,
        total_weight_kg REAL NOT NULL,
        categories TEXT,
        earnings_amount REAL NOT NULL,
        payment_status TEXT CHECK(payment_status IN ('pending','paid')) DEFAULT 'pending',
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY(request_id) REFERENCES {PICKUP_REQUESTS}(id),
        FOREIGN KEY(collector_id) REFERENCES {USERS}(id)
    );

    -- NOTIFICATIONS
    CREATE TABLE IF NOT EXISTS {NOTIFICATIONS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT CHECK(type IN ('new_request','task_assigned','collector_arrived','pickup_completed','system_alert')) NOT NULL,
        related_request_id TEXT,
        related_collection_id TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES {USERS}(id),
        FOREIGN KEY(related_request_id) REFERENCES {PICKUP_REQUESTS}(id),
        FOREIGN KEY(related_collection_id) REFERENCES {COLLECTIONS}(id)
    );

    -- EARNINGS
    CREATE TABLE IF NOT EXISTS {EARNINGS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        collector_id TEXT NOT NULL,
        collection_id TEXT NOT NULL,
        amount REAL NOT NULL,
        rate_per_kg REAL NOT NULL,
        weight_kg REAL NOT NULL,
        payment_date TEXT,
        status TEXT CHECK(status IN ('pending','processing','paid')) DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(collector_id) REFERENCES {USERS}(id),
        FOREIGN KEY(collection_id) REFERENCES {COLLECTIONS}(id)
    );

    -- WASTE PRICING
    CREATE TABLE IF NOT EXISTS {WASTE_PRICING} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        waste_type TEXT NOT NULL UNIQUE,
        price_per_kg REAL NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- DAILY METRICS
    CREATE TABLE IF NOT EXISTS {DAILY_METRICS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        metric_date TEXT NOT NULL UNIQUE,
        total_requests INTEGER DEFAULT 0,
        total_collections INTEGER DEFAULT 0,
        total_weight_kg REAL DEFAULT 0.00,
        total_earnings REAL DEFAULT 0.00,
        active_collectors INTEGER DEFAULT 0,
        active_residents INTEGER DEFAULT 0,
        avg_collection_time_minutes REAL DEFAULT 0.00,
        completion_rate REAL DEFAULT 0.00,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- TRANSACTIONS
    CREATE TABLE IF NOT EXISTS {TRANSACTIONS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        user_id TEXT,
        amount REAL,
        currency TEXT DEFAULT 'KES',
        type TEXT,
        reference TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES {USERS}(id)
    );

    -- AUDIT LOGS
    CREATE TABLE IF NOT EXISTS {AUDIT_LOGS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        actor_id TEXT,
        action TEXT,
        entity TEXT,
        entity_id TEXT,
        meta TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- LOCATIONS
    CREATE TABLE IF NOT EXISTS {LOCATIONS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        user_type TEXT,
        user_id TEXT,
        latitude REAL,
        longitude REAL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- RECYCLING CENTERS
    CREATE TABLE IF NOT EXISTS {RECYCLING_CENTERS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        name TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        contact TEXT,
        open_hours TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- WASTE REPORTS
    CREATE TABLE IF NOT EXISTS {WASTE_REPORTS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        resident_id TEXT,
        issue_type TEXT,
        description TEXT,
        photo_url TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(resident_id) REFERENCES {USERS}(id)
    );

    -- ROUTES
    CREATE TABLE IF NOT EXISTS {ROUTES} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        collector_id TEXT,
        origin TEXT,
        destination TEXT,
        distance_m INTEGER,
        duration_s INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(collector_id) REFERENCES {USERS}(id)
    );

    -- FEEDBACK
    CREATE TABLE IF NOT EXISTS {FEEDBACK} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        resident_id TEXT,
        collector_id TEXT,
        rating INTEGER,
        comments TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(resident_id) REFERENCES {USERS}(id),
        FOREIGN KEY(collector_id) REFERENCES {USERS}(id)
    );

    -- PAYMENTS
    CREATE TABLE IF NOT EXISTS {PAYMENTS} (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        resident_id TEXT,
        amount REAL,
        method TEXT,
        reference TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(resident_id) REFERENCES {USERS}(id)
    );
    """)

    conn.commit()
    conn.close()
    print("SQLite DB initialized successfully at:", DB_NAME)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def insert_user(data):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {USERS} (email, password_hash, role, full_name, phone)
        VALUES (?, ?, ?, ?, ?)
    """, (data["email"], data["password_hash"], data["role"], data["full_name"], data.get("phone")))
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {USERS} WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_pickup_request(data):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {PICKUP_REQUESTS} (resident_id, latitude, longitude, address, location_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (data["resident_id"], data["latitude"], data["longitude"], data["address"], data.get("location_notes")))
    conn.commit()
    conn.close()


def save_classification(request_id, ai_json, categories_json):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {COLLECTIONS} (request_id, collector_id, ai_classification_data, categories)
        VALUES (?, ?, ?, ?)
    """, (request_id, ai_json.get("collector_id") if isinstance(ai_json, dict) else None,
          json.dumps(ai_json), json.dumps(categories_json)))
    conn.commit()
    conn.close()
