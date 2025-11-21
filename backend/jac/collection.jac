walker DebugFlow {
    can log_entry with entry {
        print("Collection flow placeholder for MVP.")
    }
}

with entry {
    # Spawn the walker to trigger the message
    debug_walker = DebugFlow()
    root spawn debug_walker
}
