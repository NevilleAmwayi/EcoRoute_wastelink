# maps_client.py
import os
import requests

GOOGLE_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
DIST_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
DIR_URL = "https://maps.googleapis.com/maps/api/directions/json"

def get_distance_matrix(origin_list, destination_list):
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set")
    params = {"origins":"|".join(origin_list), "destinations":"|".join(destination_list), "key":GOOGLE_API_KEY, "units":"metric"}
    r = requests.get(DIST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_directions(origin, destination, waypoints=None, optimize=False):
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set")
    params = {"origin":origin, "destination":destination, "key":GOOGLE_API_KEY, "units":"metric"}
    if waypoints:
        wp = "|".join(waypoints)
        if optimize:
            wp = "optimize:true|" + wp
        params["waypoints"] = wp
    r = requests.get(DIR_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()
