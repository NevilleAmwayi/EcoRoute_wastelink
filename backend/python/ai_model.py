# ai_jac_client.py
import os
import json
import subprocess
import re

# -------------------------
# CLASSIFY IMAGE
# -------------------------
def classify_image(image_path, jac_root=None):
    """
    Classify an image using Jac CLI.
    Returns dict like {"waste_type": "plastic", "confidence": 0.9} or error dict.
    """
    params = {"image_url": image_path}

    # Build command
    cmd = ['jac', 'run', 'WasteNode.classify_image', json.dumps(params)]
    if jac_root:
        cmd.extend(['--root', jac_root])

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except Exception:
                continue
        return {"raw": out}
    except subprocess.CalledProcessError as e:
        return {"error": f"jac CLI failed: {getattr(e, 'output', str(e))}"}


# -------------------------
# CLASSIFY TEXT
# -------------------------
def classify_waste_text(text, jac_root=None):
    """
    Classify waste from text using Jac CLI, fallback to heuristics if Jac fails.
    Returns {"result": "plastic"}.
    """
    params = {"text": text}
    cmd = ['jac', 'run', 'WasteNode.classify_text', json.dumps(params)]
    if jac_root:
        cmd.extend(['--root', jac_root])

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except Exception:
                continue
        return {"raw": out}
    except subprocess.CalledProcessError:
        # Heuristic fallback
        t = text.lower()
        if "plastic" in t: return {"result": "plastic"}
        if "organic" in t or "food" in t or "banana" in t: return {"result": "organic"}
        if "glass" in t: return {"result": "glass"}
        if "paper" in t: return {"result": "paper"}
        if "metal" in t: return {"result": "metal"}
        return {"result": "mixed"}


# -------------------------
# OPTIMIZE ROUTE
# -------------------------
def optimize_route(locations, jac_root=None):
    """
    Optimize a route using Jac CLI.
    Returns a list of locations sorted by Jac node logic, or fallback to simple sorting.
    """
    if not locations:
        return []

    params = {"locations": locations}
    cmd = ['jac', 'run', 'WasteNode.optimize_route', json.dumps(params)]
    if jac_root:
        cmd.extend(['--root', jac_root])

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        for line in out.splitlines():
            try:
                return json.loads(line)
            except Exception:
                continue
        return {"raw": out}
    except subprocess.CalledProcessError:
        # Fallback: simple lat/lon sorting
        try:
            return sorted(locations, key=lambda x: f"{x.get('latitude','')},{x.get('longitude','')}")
        except Exception:
            return locations
