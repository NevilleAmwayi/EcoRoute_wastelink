extern py api from "../python/api.py";

node WeightLog {
    has collector: str;
    has material: str;
    has weight: float;
    has result: any;
}

walker LogWeight {
    # Entry ability triggered when visiting a WeightLog node
    can log with WeightLog entry {
        let data = {
            "collector": here.collector,
            "material": here.material,
            "weight": here.weight
        }

        here.result = api.api_log_weight(data)
        print(f"Weight log result: {here.result}")
    }
}

with entry {
    # Create a node for a weight log
    log_node = root ++> WeightLog(
        collector="John Doe",
        material="Plastic",
        weight=12.5
    )

    # Create walker instance
    log_walker = LogWeight()

    # Spawn walker on the node
    log_node[0] spawn log_walker

    # Show result
    print(f"Logged result: {log_node[0].result}")
}
