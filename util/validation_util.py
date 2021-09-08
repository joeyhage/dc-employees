from datetime import date, datetime
import re
from typing import cast, Dict

from werkzeug.exceptions import BadRequest, Forbidden

from util import auth_util
from util.type_util import TimecardEntry, UpdateTimecardEntryRequest, SessionIdentity


def require_float(value: str) -> None:
    if not (re.search(r'^\d+\.?\d{0,2}$', value)):
        raise BadRequest('Value must be a decimal')


def require_numeric(value: str) -> None:
    if not (re.search(r'^\d+$', value)):
        raise BadRequest('Value must be numeric')


def require_alphanumeric(value: str) -> None:
    if not (re.search(r'^[A-Za-z\d]+$', value)):
        raise BadRequest('Value must be alphanumeric')


def require_alphanumeric_space_symbols(value: str) -> None:
    if not (re.search(r'^[\w\s.,]+$', value)):
        raise BadRequest('Only letters, numbers, spaces, periods, and commas are allowed.')


def require_iso_format(value: str) -> None:
    if not (re.search(r'^\d{4}-\d{2}-\d{2}$', value)):
        raise BadRequest('Value must be in ISO format')


def verify_admin_or_self(identity: SessionIdentity, employee_id: str) -> None:
    if not (auth_util.is_admin(identity) or employee_id == identity.get('employee_id', '')):
        raise Forbidden('User not allowed to access this page. ' + str(identity))


def is_current_year(year: str) -> bool:
    return date.today().year == int(year)


def validate_employee_api_request(
        identity: SessionIdentity,
        employee_id: str,
        year: str = None,
        month: str = None,
        day: str = None
) -> None:
    require_alphanumeric(employee_id)
    if year:
        require_numeric(year)
    if month:
        require_numeric(month)
    if day:
        require_numeric(day)
    verify_admin_or_self(identity, employee_id)


def validate_timecard_entry_request(request: TimecardEntry) -> None:
    require_float(str(request.hours))
    if request.location:
        require_alphanumeric_space_symbols(request.location)
    if request.description:
        require_alphanumeric_space_symbols(request.description)
    if type(request) == UpdateTimecardEntryRequest:
        require_numeric(str(cast(UpdateTimecardEntryRequest, request).id))
    else:
        require_numeric(str(request.date))


def validate_timecard_entry_query(request: Dict[str, str]) -> None:
    if len(request.items()) != 2 or 'startDate' not in request or 'endDate' not in request:
        raise BadRequest('Timecard entry request must have startDate and endDate')
    require_iso_format(request['startDate'])
    require_iso_format(request['endDate'])
    start_date_ts = datetime.fromisoformat(request['startDate']).timestamp()
    end_date_ts = datetime.fromisoformat(request['endDate']).timestamp()
    if start_date_ts > end_date_ts:
        raise BadRequest('Start date must be before end date')
    if start_date_ts < end_date_ts - 2678400:
        raise BadRequest('Maximum time difference between start and end dates is 31 days')
