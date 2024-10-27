class HandBrakeError(Exception):
    def __init__(self, return_code: int, stderr: str):
        self.return_code = return_code
        self.stderr = stderr
        super().__init__()

    def __str__(self) -> str:
        return f"handbrake exited with return code {self.return_code}: {self.stderr}"
