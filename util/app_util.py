from util.type_util import UpdateTimecardEntryRequest, TimecardEntry

CROSS_ORIGIN_HEADERS = ['Content-Type', 'Authorization']


def get_timecard_from_request(timecard_request):
    if 'date' in timecard_request and timecard_request['date']:
        return TimecardEntry(timecard_request)
    else:
        return UpdateTimecardEntryRequest(timecard_request)
