def get_allowed_transitions(current_status):
    transitions = {
        "TODO": ["In-Progress"],
        "In-Progress": ["Waiting-For-Customer", "Resolved"],
        "Waiting-For-Customer": ["In-Progress", "Resolved"],
        "Resolved": ["Closed"],
        "Closed": [],
        "Escalated": ["In-Progress"],
    }
    return transitions.get(current_status, [])
