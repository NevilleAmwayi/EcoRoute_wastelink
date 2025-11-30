cl import from '@jac-client/utils' { jacSpawn }

node WasteItem {
  has image_url: str;
  has waste_type: str = "unknown";
  has confidence: float = 0.0;
  has collection_id: str;
}

walker ClassifyWaste {
  can classify with WasteItem entry {
    res = await jacSpawn("api_classify_image", "", {"image_url": here.image_url});

    if res.get("result") {
      parsed = res["result"];
      here.waste_type = parsed.get("waste_type", "unknown");
      here.confidence = parsed.get("confidence", 0.0);
      print(f"Classified: {here.waste_type} ({here.confidence})");
    } else if res.get("waste_type") {
      here.waste_type = res.get("waste_type", "unknown");
      here.confidence = res.get("confidence", 0.0);
      print(f"Classified (direct): {here.waste_type} ({here.confidence})");
    } else {
      print("Classification error:", res.get("error", res));
    }
    disengage;
  }
}

with entry {
  print("collector.jac demo run");
  img = root ++> WasteItem(image_url="/mnt/data/WhatsApp Image 2025-11-21 at 11.25.35 AM (1).jpeg");
  img[0] spawn ClassifyWaste;
}
