cl import from '@jac-client/utils' { jacSpawn }

node AdminStats {
  has total_users: int = 0;
  has total_requests: int = 0;
  has total_collections: int = 0;
}

walker LoadStats {
  can load with AdminStats entry {
    # Call backend walker to get stats
    stats = await jacSpawn("api_get_stats", "", {});
    here.total_users = stats.get("total_users", 0);
    here.total_requests = stats.get("total_requests", 0);
    here.total_collections = stats.get("total_collections", 0);

    print(f"Admin stats - users: {here.total_users}, requests: {here.total_requests}, collections: {here.total_collections}");
    disengage;
  }
}

with entry {
  print("admin.jac demo run");
  a = root ++> AdminStats();
  a[0] spawn LoadStats;
}
