from unittest import TestCase

from app_util import get_timecard_from_request
from util.type_util import TimecardEntry, UpdateTimecardEntryRequest


class Test(TestCase):
    def test_get_timecard_from_request_given_update(self):
        timecard_request = {'id': 14, 'date': None, 'hours': 5, 'location': 'abc', 'description': 'test ted gsg sfg sfg'}
        timecard = get_timecard_from_request(timecard_request)
        self.assertEqual(UpdateTimecardEntryRequest, type(timecard))

    def test_get_timecard_from_request_given_insert(self):
        timecard_request = {'date': 123, 'hours': 5, 'location': 'abc', 'description': 'test ted gsg sfg sfg'}
        timecard = get_timecard_from_request(timecard_request)
        self.assertEqual(TimecardEntry, type(timecard))
