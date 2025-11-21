extern py api from "../python/api.py";

node TasksNode {
    has tasks: list[str] = []
}

walker Tasks {
    # Entry ability triggered when visiting a TasksNode
    can fetch_tasks with TasksNode entry {
        here.tasks = api.api_get_tasks()
        print(f"Tasks fetched: {here.tasks}")
    }
}

with entry {
    # Create a node to hold tasks
    tasks_node = root ++> TasksNode()

    # Create walker instance
    tasks_walker = Tasks()

    # Spawn walker on the node
    tasks_node[0] spawn tasks_walker

    # Show tasks
    print(f"Node tasks: {tasks_node[0].tasks}")
}
