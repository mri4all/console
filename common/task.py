import json

# Incomplete


def read_task_file(filename):
    """
    Reads the task file in json format and returns a dictionary.
    """
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error reading task file: {}".format(e))
        return None
