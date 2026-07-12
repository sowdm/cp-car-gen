import pytest

from cp_cars_generator import set_day, CAR_GROUP_WORKSHEET

NDAYS = 4

def test_overwrite_before_start():
    worksheet_list = []
    with pytest.raises(AssertionError):
        set_day('overwrite', worksheet_list, NDAYS)


def test_first_day():
    worksheet_list = []
    day = set_day('next', worksheet_list, NDAYS)
    assert day==1


def test_first_day_overwrite():
    worksheet_list = [CAR_GROUP_WORKSHEET.format(1)]
    day = set_day('overwrite', worksheet_list, NDAYS)
    assert day==1


def test_last_day():
    worksheet_list = [CAR_GROUP_WORKSHEET.format(k) for k in range(1,NDAYS)]
    day = set_day('next', worksheet_list, NDAYS)
    assert day==NDAYS
    

def test_last_day_overwrite():
    worksheet_list = [CAR_GROUP_WORKSHEET.format(k) for k in range(1,NDAYS+1)]
    day = set_day('overwrite', worksheet_list, NDAYS)
    assert day==NDAYS


def test_trip_complete():
    worksheet_list = [CAR_GROUP_WORKSHEET.format(k) for k in range(1,NDAYS+1)]
    with pytest.raises(AssertionError):
        set_day('next', worksheet_list, NDAYS)


@pytest.mark.parametrize('mode', ['next','overwrite'])
def test_next_bad_format(mode):
    worksheet_list = [CAR_GROUP_WORKSHEET.format(k) for k in range(2,NDAYS)]
    with pytest.raises(AssertionError):
        set_day(mode, worksheet_list, NDAYS)