class HandBrakeError(Exception):
    def __init__(self, return_code: int):
        super().__init__()
        self.return_code = return_code

    def __str__(self) -> str:
        return "handbrake exited with return code " + str(self.return_code)
