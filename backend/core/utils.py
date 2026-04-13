import numpy as np

def sanitize_for_json(obj):
    """
    Recursively converts numpy types in a dictionary or list to standard Python types
    so they can be JSON serialized by FastAPI/Pydantic.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(x) for x in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.datetime64, np.timedelta64)):
        return str(obj)
    return obj
