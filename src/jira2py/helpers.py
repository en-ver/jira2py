from typing import Any


def clean_none_values(data: Any) -> dict[str, Any] | list[Any] | None:
    """Recursively remove keys with falsy values from nested dictionaries and lists."""
    if data is None:
        return None
    elif isinstance(data, dict):
        return {k: clean_none_values(v) for k, v in data.items() if v}
    elif isinstance(data, list):
        return [clean_none_values(item) for item in data if item]
    else:
        return data
