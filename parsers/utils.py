

def to_form_data(data: dict) -> dict:
    result = dict()
    for k, v in data.items():
        result[k] = (None, v)
    return result
