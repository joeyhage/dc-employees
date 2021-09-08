from typing import Dict

from flask import current_app, Blueprint, jsonify, request
from flask_cors import cross_origin
from werkzeug.exceptions import Forbidden

from app import app_db
from util.app_util import CROSS_ORIGIN_HEADERS, get_timecard_from_request
from util.type_util import SessionIdentity, UpdateTimecardEntryRequest
from util import app_logger, auth_util, validation_util

employee = Blueprint('employee', __name__)
logger = app_logger.create_logger('employee', current_app.config['IS_DEV'])
requires_auth = auth_util.init_auth('employee')


@employee.route('/list', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True, with_session=True)
def get_employee_list():
    logger.info('GET /api/employee/list')
    employee_list = app_db().employee_list()
    return jsonify(employee_list)


@employee.route('/<employee_id>/info', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def get_employee_info(identity: SessionIdentity, employee_id: str):
    validation_util.validate_employee_api_request(identity, employee_id)
    logger.info('GET /api/employee/%s/info', employee_id)

    try:
        return jsonify(app_db().employee_info(employee_id))
    except TypeError as e:
        if auth_util.is_admin(identity):
            return jsonify({})
        else:
            logger.info(f"Employee {identity['name']} does not exist. Creating new employee...", exc_info=e)
            [first_name, last_name] = identity['name'].split(' ')
            data = {
                'id': identity['employee_id'],
                'first_name': first_name,
                'last_name': last_name,
                'user_principal_name': identity['user_principal_name'],
                'new_employee': True
            }
            app_db().create_employee(data)
            return jsonify(data)


@employee.route('/<employee_id>/timecard/hours/<year>/<month>', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def get_timecard_hours(identity: SessionIdentity, employee_id: str, year: str, month: str):
    validation_util.validate_employee_api_request(identity, employee_id, year, month)
    logger.info('GET /api/employee/%s/timecard/hours/%s/%s', employee_id, year, month)

    if auth_util.is_admin(identity) or validation_util.is_current_year(year):
        return jsonify(app_db().get_daily_hours_worked(employee_id, year, month))
    else:
        logger.info('Employee %s does not have permission to view %s-%s-%s', employee_id, year, month)
        return jsonify([])


@employee.route('/<employee_id>/timecard/entries/<year>/<month>/<day>', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def get_timecard_entries(identity: SessionIdentity, employee_id: str, year: str, month: str, day: str):
    validation_util.validate_employee_api_request(identity, employee_id, year, month, day)
    logger.info('GET /api/employee/%s/timecard/entries/%s/%s/%s', employee_id, year, month, day)

    if auth_util.is_admin(identity) or validation_util.is_current_year(year):
        return jsonify(app_db().get_timecard_entries(employee_id, year, month, day))
    else:
        logger.info('Employee %s does not have permission to view %s-%s-%s', employee_id, year, month, day)
        return jsonify([])


@employee.route('/<employee_id>/timecard/entries/report', methods=['POST'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def timecard_entry_report(identity: SessionIdentity, employee_id: str):
    request_dates: Dict[str, str] = request.json
    validation_util.validate_employee_api_request(identity, employee_id)
    validation_util.validate_timecard_entry_query(request_dates)
    logger.info('POST /api/employee/%s/timecard/entries/report - %s', employee_id, str(request_dates))

    return jsonify(
        app_db().get_timecard_entries_between(employee_id, request_dates['startDate'], request_dates['endDate']))


@employee.route('/<employee_id>/timecard', methods=['PUT'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def post_timecard_entry(identity: SessionIdentity, employee_id: str):
    timecard = get_timecard_from_request(request.json)
    validation_util.validate_employee_api_request(identity, employee_id)
    validation_util.validate_timecard_entry_request(timecard)
    logger.info('PUT /api/employee/%s/timecard - %s', employee_id, str(timecard.__dict__))

    if type(timecard) == UpdateTimecardEntryRequest:
        existing_timecard = app_db().get_timecard_by_id(timecard.id)
        if auth_util.is_admin(identity) or employee_id == existing_timecard['employee_id']:
            timecard.date = existing_timecard['timecard_date']
            timecard.employee_id = employee_id
            successful = app_db().update_timecard(timecard, identity['name'])
            logger.info('Error updating timecard, returning 500')
            return jsonify({}), (204 if successful else 500)
    else:
        timecard.employee_id = employee_id
        app_db().create_timecard(timecard, identity['name'])
        return jsonify({}), 204
    raise Forbidden(f'Employee {employee_id} does not have permission to post a new timecard entry')


@employee.route('/<employee_id>/timecard/<timecard_id>', methods=['DELETE'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(with_session=True)
def delete_timecard_entry(identity: SessionIdentity, employee_id: str, timecard_id: str):
    validation_util.validate_employee_api_request(identity, employee_id)
    logger.info('DELETE /api/employee/%s/timecard/%s', employee_id, timecard_id)

    existing_timecard = app_db().get_timecard_by_id(timecard_id)
    if auth_util.is_admin(identity) or employee_id == existing_timecard['employee_id']:
        successful = app_db().delete_timecard(timecard_id)
        logger.info('Error deleting timecard, returning 500')
        return jsonify({}), (204 if successful else 500)
    else:
        raise Forbidden(f'Employee {employee_id} does not have permission to delete new timecard entry {timecard_id}')
