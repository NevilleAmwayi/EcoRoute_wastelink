# api.py
import os
import json
import subprocess
from utils import connect, init_db
from maps_client import get_distance_matrix, get_directions
from ai_model import classify_image, classify_waste_text, optimize_route

# init DB
init_db()

# try jac-client
try:
    from jac_client import JacClient
    JAC_CLIENT_PRESENT = True
    JC = JacClient()  # optional root_dir can be passed if needed
except Exception:
    JacClient = None
    JAC_CLIENT_PRESENT = False
    JC = None


def _run_jac_client(node, action, params=None):
    if not JAC_CLIENT_PRESENT:
        return {"error": "jac-client not available"}
    try:
        # prefer run_node if available
        if hasattr(JC, "run_node"):
            return JC.run_node(node, action, params or {})
        # else try generic run
        if hasattr(JC, "run"):
            return JC.run(f"{node}.{action}", params or {})
        return {"error": "jac-client has no known run method"}
    except Exception as e:
        return {"error": str(e)}


def run_jac(node_name, action, params=None):
    """
    Use jac-client if present, otherwise fallback to CLI.
    """
    if JAC_CLIENT_PRESENT:
        res = _run_jac_client(node_name, action, params)
        # if jac-client returned something meaningful, return it
        if isinstance(res, dict):
            return res
        # else try CLI fallback
    params_json = json.dumps(params) if params else "{}"
    cmd = f'jac run {node_name}.{action} "{params_json}"'
    try:
        result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        for line in result.splitlines():
            try:
                return json.loads(line)
            except Exception:
                continue
        return {"raw": result}
    except subprocess.CalledProcessError as e:
        return {"error": str(e), "output": getattr(e, "output", "")}


# -------------------------
# AUTH
# -------------------------
def api_auth(email, password_hash):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id, email, role, full_name FROM users WHERE email=? AND password_hash=?", (email, password_hash))
    row = cur.fetchone(); conn.close()
    return dict(row) if row else {"error": "Invalid credentials"}


# -------------------------
# CREATE PICKUP REQUEST
# -------------------------
def api_create_request(data):
    conn = connect(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO pickup_requests (resident_id, latitude, longitude, address, location_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (data["resident_id"], data["latitude"], data["longitude"], data["address"], data.get("location_notes")))
    conn.commit()
    cur.execute("SELECT id FROM pickup_requests ORDER BY rowid DESC LIMIT 1")
    rid = cur.fetchone()[0]; conn.close()
    return {"status": "saved", "request_id": rid}


# -------------------------
# GET TASKS
# -------------------------
def api_get_tasks(collector_id=None, max_items=10):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id, latitude, longitude, address FROM pickup_requests WHERE status='pending'")
    rows = cur.fetchall(); conn.close()
    tasks = [dict(r) for r in rows]
    if not tasks:
        return {"tasks": []}

    if collector_id:
        conn = connect(); cur = conn.cursor()
        cur.execute("SELECT collector_latitude AS lat, collector_longitude AS lng FROM users WHERE id=?", (collector_id,))
        col = cur.fetchone(); conn.close()
        if col and col["lat"] is not None and col["lng"] is not None and os.environ.get("GOOGLE_MAPS_API_KEY"):
            origin = f"{col['lat']},{col['lng']}"
            destinations = [f"{t['latitude']},{t['longitude']}" for t in tasks]
            try:
                dm = get_distance_matrix([origin], destinations)
                elements = dm["rows"][0]["elements"]
                distances = []
                for i, el in enumerate(elements):
                    meters = el["distance"]["value"] if el.get("status") == "OK" else 10**9
                    distances.append((meters, tasks[i]))
                distances.sort(key=lambda x: x[0])
                ordered = [t for _, t in distances][:max_items]
                return {"tasks": ordered}
            except Exception:
                pass

    tasks_sorted = sorted(tasks, key=lambda t: (t["latitude"], t["longitude"]))[:max_items]
    return {"tasks": tasks_sorted}


# -------------------------
# ASSIGN COLLECTOR
# -------------------------
def api_assign_collector(request_id):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT latitude, longitude FROM pickup_requests WHERE id=?", (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close(); return {"error": "request not found"}

    cur.execute("SELECT id, collector_latitude AS lat, collector_longitude AS lng FROM users WHERE role='collector' AND is_available=1 AND collector_latitude IS NOT NULL")
    collectors = cur.fetchall()
    if not collectors:
        conn.close(); return {"error": "no collectors available"}

    origin = f"{req['latitude']},{req['longitude']}"
    destinations = [f"{c['lat']},{c['lng']}" for c in collectors]
    try:
        dm = get_distance_matrix([origin], destinations)
        elems = dm["rows"][0]["elements"]
        best_i = None
        best_dist = 10**12
        for i, el in enumerate(elems):
            d = el["distance"]["value"] if el.get("status") == "OK" else 10**12
            if d < best_dist:
                best_dist = d; best_i = i
        chosen = collectors[best_i]
        chosen_id = chosen["id"]
        cur.execute("UPDATE pickup_requests SET assigned_collector_id=?, status='assigned', assigned_at=CURRENT_TIMESTAMP WHERE id=?", (chosen_id, request_id))
        conn.commit(); conn.close()
        return {"assigned_collector_id": chosen_id, "distance_m": best_dist}
    except Exception as e:
        conn.close(); return {"error": str(e)}


# -------------------------
# LOG WEIGHT / CREATE COLLECTION
# -------------------------
def api_log_weight(data):
    conn = connect(); cur = conn.cursor()
    ai_data = None
    if data.get("waste_photo_url"):
        try:
            ai_data = classify_image(data["waste_photo_url"])
        except Exception as e:
            ai_data = {"error": str(e)}

    earnings_amount = None
    wt = None
    if isinstance(ai_data, dict):
        if ai_data.get("waste_type"):
            wt = ai_data.get("waste_type")
        elif ai_data.get("result") and isinstance(ai_data["result"], dict):
            wt = ai_data["result"].get("waste_type")

    if wt:
        cur.execute("SELECT price_per_kg FROM waste_pricing WHERE waste_type=? AND is_active=1", (wt,))
        p = cur.fetchone()
        if p:
            earnings_amount = p[0] * float(data["total_weight_kg"])
    if earnings_amount is None:
        earnings_amount = 5.0 * float(data["total_weight_kg"])

    cur.execute("""
      INSERT INTO collections (request_id, collector_id, waste_photo_url, ai_classification_data, total_weight_kg, categories, earnings_amount, payment_status)
      VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        data["request_id"],
        data["collector_id"],
        data.get("waste_photo_url"),
        json.dumps(ai_data) if ai_data else None,
        data["total_weight_kg"],
        None,
        earnings_amount
    ))
    conn.commit()
    cur.execute("SELECT id FROM collections ORDER BY rowid DESC LIMIT 1")
    cid = cur.fetchone()[0]

    cur.execute("""
      INSERT INTO earnings (collector_id, collection_id, amount, rate_per_kg, weight_kg, status)
      VALUES (?, ?, ?, ?, ?, 'pending')
    """, (data["collector_id"], cid, earnings_amount, earnings_amount / float(data["total_weight_kg"]), data["total_weight_kg"]))

    cur.execute("UPDATE pickup_requests SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?", (data["request_id"],))
    conn.commit(); conn.close()
    return {"status": "logged", "collection_id": cid, "earnings_amount": earnings_amount, "ai_data": ai_data}


# -------------------------
# WRAPPERS: CLASSIFY / OPTIMIZE
# -------------------------
def api_classify_waste_text(text):
    return classify_waste_text(text)

def api_classify_image(image_url):
    return classify_image(image_url)

def api_optimize_route_for_collector(collector_id, max_items=10):
    tasks_resp = api_get_tasks(collector_id=collector_id, max_items=max_items)
    tasks = tasks_resp.get("tasks", [])
    if not tasks:
        return {"route": []}
    return optimize_route(tasks)
    

# -------------------------
# ADMIN STATS
# -------------------------
def api_get_stats():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total_users FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) AS total_requests FROM pickup_requests")
    requests = cur.fetchone()[0]
    conn.close()
    return {"total_users": users, "total_requests": requests}
