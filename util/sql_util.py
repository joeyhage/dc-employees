from typing import List
from os import environ

from datetime import datetime

from util.type_util import UpdateTimecardEntryRequest, TimecardEntry

MYSQL_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def format_year_month_day_as_iso(year: str, month: str, day: str) -> str:
    formatted_month = f'{int(month):02d}'
    formatted_day = f'{int(day):02d}'
    return f'{year}-{formatted_month}-{formatted_day}'


class SQLUtil:

    def __init__(self, db):
        self.db = db

    def get_db(self):
        return self.db

    def employee_list(self) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT id,
                       first_name,
                       last_name
                FROM employee
            ''').fetchall()
        )

    def employee_info(self, employee_id) -> dict:
        return dict(
            self.db.session.execute(f'''
                SELECT id,
                       first_name,
                       last_name,
                       user_principal_name
                FROM employee
                WHERE id = :employee_id
            ''', {'employee_id': employee_id}).fetchone()
        )

    def create_employee(self, employee_data: dict) -> None:
        self.db.session.execute(f'''
            INSERT INTO employee (id, first_name, last_name, user_principal_name)
            VALUES (:employee_id, :first_name, :last_name, :user_principal_name)
        ''', {
            'employee_id': employee_data['id'],
            'first_name': employee_data['first_name'],
            'last_name': employee_data['last_name'],
            'user_principal_name': employee_data['user_principal_name']
        })

    def get_daily_hours_worked(self, employee_id: str, year: str, month: str) -> List[dict]:
        if int(month) == 12:
            next_month = format_year_month_day_as_iso(str(int(year) + 1), '1', '1')
        else:
            next_month = format_year_month_day_as_iso(year, str(int(month) + 1), '1')
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT timecard_date,
                       SUM(hours) as total_hours
                FROM timecard
                WHERE employee_id = :employee_id
                AND timecard_date >= :month_start
                AND timecard_date < :next_month
                GROUP BY timecard_date
            ''', {
                'employee_id': employee_id,
                'month_start': format_year_month_day_as_iso(year, month, '1'),
                'next_month': next_month
            }).fetchall()
        )

    def get_timecard_entries(self, employee_id: str, year: str, month: str, day: str) -> List[dict]:
        date_to_query = format_year_month_day_as_iso(year, month, day)
        return self.get_timecard_entries_between(employee_id, date_to_query, date_to_query)

    def get_timecard_entries_between(self, employee_id: str, start_date: str, end_date: str) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT id,
                       timecard_date,
                       hours,
                       location,
                       description,
                       created_ts,
                       modified_ts,
                       created_by,
                       last_modified_by
                FROM timecard
                WHERE employee_id = :employee_id
                AND timecard_date >= :start_date
                AND timecard_date <= :end_date
            ''', {
                'employee_id': employee_id,
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
        )

    def get_timecard_by_id(self, timecard_id) -> dict:
        return dict(
            self.db.session.execute(f'''
                SELECT employee_id,
                       timecard_date
                FROM timecard
                WHERE id = :id
            ''', {'id': int(timecard_id)}).fetchone()
        )

    def create_timecard(self, timecard: TimecardEntry, name: str) -> None:
        now = datetime.now().strftime(MYSQL_TIME_FORMAT)
        return self.db.session.execute(f'''
            INSERT INTO timecard (
                employee_id, 
                timecard_date,
                hours,
                location,
                description,
                created_ts,
                modified_ts,
                created_by,
                last_modified_by
            ) VALUES (
                :employee_id, 
                :timecard_date,
                :hours,
                :location,
                :description,
                :created_ts,
                :modified_ts,
                :created_by,
                :last_modified_by
            )
        ''', {
            'employee_id': timecard.employee_id,
            'timecard_date': datetime.fromtimestamp(timecard.date).strftime(MYSQL_TIME_FORMAT),
            'hours': float(timecard.hours),
            'location': timecard.location,
            'description': timecard.description,
            'created_ts': now,
            'modified_ts': now,
            'created_by': name,
            'last_modified_by': name
        })

    def update_timecard(self, timecard: UpdateTimecardEntryRequest, name: str) -> bool:
        return self.db.session.execute(f'''
            UPDATE timecard 
            SET 
                hours = :hours,
                location = :location,
                description = :description,
                modified_ts = :modified_ts,
                last_modified_by = :last_modified_by
            WHERE id = :id
        ''', {
            'id': int(timecard.id),
            'hours': float(timecard.hours),
            'location': timecard.location,
            'description': timecard.description,
            'modified_ts': datetime.now().strftime(MYSQL_TIME_FORMAT),
            'last_modified_by': name
        }).rowcount == 1

    def delete_timecard(self, timecard_id) -> bool:
        return self.db.session.execute(f'''
            DELETE FROM timecard 
            WHERE id = :id
        ''', {'id': int(timecard_id)}).rowcount == 1

    @staticmethod
    def rows_to_dict_list(row_proxy) -> List[dict]:
        return list(map(lambda row: dict(row), row_proxy))


# noinspection PyUnresolvedReferences
def init_db(app) -> SQLUtil:
    from flask_sqlalchemy import SQLAlchemy

    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqldb://{environ["DB_USER"]}:{environ["DB_PASS"]}@localhost/{environ["DB_NAME"]}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600

    return SQLUtil(SQLAlchemy(app))
