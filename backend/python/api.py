from utils import connect
from ai_model import classify_waste, optimize_route


# -------------------------
# USER AUTHENTICATION
# -------------------------
def api_auth(username, password):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT id, role FROM users WHERE username=? AND password=?", 
                (username, password))
    row = cur.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "role": row[1]}
    
    return {"error": "Invalid credentials"}



# -------------------------
# CREATE REQUEST (Resident)
# -------------------------
def api_create_request(data):
    auto_type = classify_waste(data["description"])

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO requests (user, location, description, waste_type, status)
        VALUES (?, ?, ?, ?, ?)
    """, (data["user"], data["location"], data["description"], auto_type, "pending"))

    conn.commit()
    conn.close()

    data["auto_classified_type"] = auto_type
    return {"status": "saved", "data": data}



# -------------------------
# GET COLLECTOR TASKS
# -------------------------
def api_get_tasks():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT id, location FROM requests WHERE status='pending'")
    rows = cur.fetchall()
    conn.close()

    locations = [row[1] for row in rows]
    optimized = optimize_route(locations)

    return {"optimized_route": optimized}



# -------------------------
# LOG WEIGHT (Admin)
# -------------------------
def api_log_weight(data):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO weights (collector, material, weight)
        VALUES (?, ?, ?)
    """, (data["collector"], data["material"], data["weight"]))

    conn.commit()
    conn.close()

    return {"status": "logged"}
