import gspread
import pytest

@pytest.fixture(scope='session')
def client():
    return gspread.service_account()