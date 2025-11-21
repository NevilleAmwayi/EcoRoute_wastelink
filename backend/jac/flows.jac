node User {
    has name: str;
}

node Request {
    has id: int;
    has status: str = "pending";
}

walker WasteLinkRouter {
    has visited: list[str] = [];

    # Auth ability triggered when visiting a User
    can auth with User entry {
        print(f"Authenticating user {here.name}");
        self.visited.append(f"auth: {here.name}");
    }

    # Create request ability triggered when visiting a Request
    can create_request with Request entry {
        print(f"Creating request {here.id}");
        here.status = "created";
        self.visited.append(f"create_request: {here.id}");
    }

    # Tasks ability triggered when visiting a User
    can tasks with User entry {
        print(f"Listing tasks for user {here.name}");
        self.visited.append(f"tasks: {here.name}");
    }

    # Log weight ability triggered when visiting a User
    can log_weight with User entry {
        print(f"Logging weight for user {here.name}");
        self.visited.append(f"log_weight: {here.name}");
    }
}

with entry {
    # Create nodes
    alice = root ++> User(name="Alice");
    bob = root ++> User(name="Bob");
    req1 = root ++> Request(id=101);

    # Create walker
    router = WasteLinkRouter();

    # Spawn walker on nodes
    alice[0] spawn router;
    bob[0] spawn router;
    req1[0] spawn router;

    # Show visited log
    print(f"Visited locations: {router.visited}");
}
