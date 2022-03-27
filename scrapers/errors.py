

class HtmlParsingError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ApiResponseError(Exception):
    def __init__(self, message: str = 'API returned error'):
        self.message = message
        super().__init__(self.message)


class InvalidStationError(Exception):
    def __init__(self, station: str):
        self.station = station
        self.message = f'invalid station: {station}'
        super().__init__(self.message)


class InvalidFuelError(Exception):
    def __init__(self, fuel: str):
        self.fuel = fuel
        self.message = f'invalid fuel: {fuel}'
        super().__init__(self.message)
