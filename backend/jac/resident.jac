cl import from '@jac-client/utils' { jacSpawn }

node ResidentRequest {
  has resident_id: str;
  has address: str;
  has latitude: float;
  has longitude: float;
  has location_notes: str = "";
  has pickup_id: str;
}

walker RequestPickup {
  can request with ResidentRequest entry {
    pid = await jacSpawn("api_create_request", "", {
      "resident_id": here.resident_id,
      "latitude": here.latitude,
      "longitude": here.longitude,
      "address": here.address,
      "location_notes": here.location_notes
    });

    here.pickup_id = pid.get("request_id");
    print(f"Pickup created: {here.pickup_id}");
    disengage;
  }
}

with entry {
  print("resident.jac demo run");
  r = root ++> ResidentRequest(resident_id="res-demo", address="Demo Address", latitude=-1.2921, longitude=36.8219);
  r[0] spawn RequestPickup;
}
