import os
import __main__ as main

service_name = "unknown"
base_path = os.path.dirname(os.path.realpath(main.__file__))
current_task_id = ""


def set_service_name(name):
    """Set the service name. This is used across the framework to identify the current service."""
    global service_name
    service_name = name


def get_service_name():
    """Get the service name."""
    return service_name


def get_base_path():
    """Get the base path of the MRI4ALL installation."""
    return base_path


def set_current_task_id(task_id: str):
    """Set the currently processed task ID."""
    global current_task_id
    current_task_id = task_id


def get_current_task_id() -> str:
    """Get the currently processed task ID. If no task is currently processed, an empty string is returned."""
    global current_task_id
    return current_task_id


def clear_current_task_id():
    """Clear the currently processed task ID."""
    global current_task_id
    current_task_id = ""
