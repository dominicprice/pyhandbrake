from handbrake.models.common import HandBrakeModel


class VersionIdentifier(HandBrakeModel):
    major: int
    minor: int
    point: int


class Version(HandBrakeModel):
    arch: str
    name: str
    official: bool
    repo_date: str
    repo_hash: str
    system: str
    type: str
    version: VersionIdentifier
    version_string: str
