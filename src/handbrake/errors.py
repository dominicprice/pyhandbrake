class HandBrakeError(Exception):
    def __init__(self, return_code: int, stderr: str):
        super().__init__()

        self.return_code = return_code
        self.stderr = stderr

        if "No title found." in stderr:
            self.message = "no title found"
        elif "Invalid preset" in stderr:
            self.message = "invalid preset"
        else:
            self.message = "see stderr"

    def __str__(self) -> str:
        return f"handbrake exited with return code {self.return_code}: {self.message}"
