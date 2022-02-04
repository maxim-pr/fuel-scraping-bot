from yaml import load, SafeLoader


def load_config() -> dict:
    with open('parsers/config/config.yml', 'r') as file:
        data = load(file, Loader=SafeLoader)
    return data
