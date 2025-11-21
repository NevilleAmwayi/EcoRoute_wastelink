extern py api from "../python/api.py";

node RequestNode {
    has user: str;
    has location: str;
    has description: str;
    has response: str = "";
}

walker CreateRequest {
    has user: str;
    has location: str;
    has description: str;

    # Entry ability triggered when visiting a RequestNode
    can create with RequestNode entry {
        let data = {
            "user": self.user,
            "location": self.location,
            "description": self.description
        }

        here.response = api.api_create_request(data)
        print(f"Request created: {here.response}")
    }
}

with entry {
    # Create a request node
    req_node = root ++> RequestNode(user="Alice", location="Nairobi", description="Pickup waste")

    # Create walker
    walker_instance = CreateRequest(user="Alice", location="Nairobi", description="Pickup waste")

    # Spawn walker on the node
    req_node[0] spawn walker_instance

    # Show response
    print(f"Node response: {req_node[0].response}")
}
