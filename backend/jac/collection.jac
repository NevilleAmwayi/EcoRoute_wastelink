cl import from '@jac-client/utils' { jacSpawn }

node Collection {
  has request_id: str;
  has collector_id: str;
  has total_weight_kg: float;
  has waste_photo_url: str;
  has categories: dict = {};
  has collection_id: str;
  has earnings_amount: float;
}

walker SaveCollection {
  can save with Collection entry {
    payload = {
      "request_id": here.request_id,
      "collector_id": here.collector_id,
      "waste_photo_url": here.waste_photo_url,
      "total_weight_kg": here.total_weight_kg,
      "notes": ""
    };

    res = await jacSpawn("api_log_weight", "", payload);
    if res.get("status") == "logged" {
      here.collection_id = res.get("collection_id");
      here.earnings_amount = res.get("earnings_amount", 0.0);
      print(f"Saved collection {here.collection_id} earnings {here.earnings_amount}");
    } else {
      print("Save collection failed:", res);
    }
    disengage;
  }
}

with entry {
  print("collection.jac demo run");
  c = root ++> Collection(request_id="req-demo", collector_id="col-demo", total_weight_kg=4.2, waste_photo_url="/mnt/data/WhatsApp Image 2025-11-21 at 11.25.35 AM (1).jpeg");
  c[0] spawn SaveCollection;
}
