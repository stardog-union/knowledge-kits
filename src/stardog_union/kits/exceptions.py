class InvalidKit(Exception):
    pass


class InvalidDataSource(InvalidKit):
    def __init__(self, ds_name: str):
        self.message = f"Source {ds_name} specified for a virtual graph does not exist. Check your configuration and try again."
        super().__init__(self.message)
