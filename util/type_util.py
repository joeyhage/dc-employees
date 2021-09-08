from typing import TypedDict, List


class JWTClaims(TypedDict):
    aud: str
    iss: str
    iat: int
    exp: int
    groups: List[str]
    ipaddr: str
    name: str
    oid: str
    tid: str
    unique_name: str
    upn: str


class SessionIdentity(TypedDict):
    employee_id: str
    exp: int
    is_admin: bool
    name: str
    payload: JWTClaims
    user_principal_name: str


class TimecardEntry:
    def __init__(self, timecard):
        self._hours: float = timecard['hours']
        self._location: str = timecard['location']
        self._description: str = timecard['description'] if 'description' in timecard else None
        self._date: int = timecard['date'] if 'date' in timecard else None
        self._employee_id = None

    @property
    def hours(self):
        return self._hours

    @hours.setter
    def hours(self, hours):
        self._hours = hours

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        self._date = date

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, employee_id):
        self._employee_id = employee_id


class UpdateTimecardEntryRequest(TimecardEntry):
    def __init__(self, timecard):
        super().__init__(timecard)
        self._id: int = timecard['id']

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, timecard_id):
        self._id = timecard_id
