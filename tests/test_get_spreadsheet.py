import pandas as pd
import pytest

from mock_gspread import set_mockreturn
from cp_gsheet import get_spreadsheet
from worksheets import SHEET_INDICATOR, FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, DRIVER_WORKSHEET, CAR_GROUP_WORKSHEET
import constants
import columns

data = {
    'First Name':['First1','First2'],
    'Last Name':['Last1','Last2'],
    'Will Be A Driver':['Yes','No'],
    'Willing To Be Backup Car':['No','Yes'],
    'Will Have Car On The Ground':['Yes','Yes'],
    columns.HALF_DAY_COL:['',''],
    columns.AFFILIATION_COL:['','Action Academy (Graduate or Current Participate)'],
    columns.DATES_COL:['5/16/2026\n5/17/2026\n5/18/2026\n5/19/2026','5/16/2026\n5/17/2026\n5/18/2026'],
    columns.GENERATION_COL:['Boomer (1946 - 1964)','Gen Z (1995 - 2012)'],
    columns.BIPOC_COL:['No','Yes'],
    columns.EXPERIENCE_COL:['I have a lot, but not with CP','None'],
}
df_full_roster = pd.DataFrame(data)

df_roster = df_full_roster[columns.ORIG_COLS]
df_roster = df_roster.rename(columns=columns.RENAME_COLS)
df_roster[columns.NAME_COL] = df_roster.apply(lambda x: f"{x[columns.NAME_COL]} {x['Last Name']}", axis=1)

dates = df_roster[columns.DATES_COL].tolist()
dates = [x.strip().split() for x in dates]
date_set = set()
for d in dates:
    date_set.update(d)
all_dates = list(set(pd.to_datetime(x) for x in date_set))
all_dates.sort()

day_cols = []
for k,d in enumerate(all_dates):
    day_cols.append(f'Day {k+1} ({d.strftime('%a')})')
    df_roster[day_cols[-1]] = df_roster[columns.DATES_COL].apply(lambda x: constants.MARK if d in [pd.to_datetime(x) for x in x.strip().split()] else '')

df_roster = df_roster.drop(columns=columns.DELETE_COLS)

drivers = {columns.NAME_COL:[], columns.DRIVER_TYPE_COL:[]}
for k in df_roster.index:
    if df_roster.loc[k, 'Driver'].lower()=='yes':
        drivers[columns.NAME_COL].append(df_roster.loc[k, columns.NAME_COL])
        drivers[columns.DRIVER_TYPE_COL].append(constants.PREFERRED_DRIVER)
    elif df_roster.loc[k, 'Backup Driver'].lower()=='yes':
        drivers[columns.NAME_COL].append(df_roster.loc[k, columns.NAME_COL])
        drivers[columns.DRIVER_TYPE_COL].append(constants.BACKUP_DRIVER)
df_drivers = pd.DataFrame(drivers)
for c in day_cols:
    df_drivers[c] = ''


@pytest.mark.parametrize('worksheets',[[], ['WS1','WS2']])
def test_worksheets_no_cp_spreadsheets(monkeypatch, client, worksheets):
    set_mockreturn(client, monkeypatch, worksheets)

    url = 'FAKE'
    gsheet = get_spreadsheet(client, url)

    assert gsheet['url']==url
    assert gsheet['worksheets']==[]
    assert not gsheet['has_cp_export']
    assert not gsheet['is_init']


def test_worksheets_has_cp_spreadsheets(monkeypatch, client):

    cpworksheets = [f'{SHEET_INDICATOR}WS1',f'{SHEET_INDICATOR}WS2']
    worksheets = ['NOT_CP']
    worksheets.extend(cpworksheets)
    set_mockreturn(client, monkeypatch, worksheets)

    url = 'FAKE'
    gsheet = get_spreadsheet(client, url)

    assert gsheet['url']==url
    assert gsheet['worksheets']==cpworksheets
    assert not gsheet['has_cp_export']
    assert not gsheet['is_init']


@pytest.mark.parametrize('worksheets', [[], ['FAKE']])
def test_has_cp_export(monkeypatch, client, worksheets):

    worksheets.append(FULL_ROSTER_WORKSHEET)
    dfs = [df_full_roster if w==FULL_ROSTER_WORKSHEET else [] for w in worksheets]
    set_mockreturn(client, monkeypatch, worksheets, dfs)

    url = 'FAKE'
    gsheet = get_spreadsheet(client, url)

    assert gsheet['has_cp_export']
    assert not gsheet['is_init']
    assert gsheet['worksheets']==[FULL_ROSTER_WORKSHEET]
    assert gsheet['dates']==all_dates
    assert not any(gsheet['date_has_car_group'])
    assert not gsheet['car_group_date_error']
    assert not gsheet['is_complete']


def test_is_init(monkeypatch, client):
    worksheets = [FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, DRIVER_WORKSHEET]
    dfs = [df_full_roster, df_roster, df_drivers]
    set_mockreturn(client, monkeypatch, worksheets, dfs)

    url = 'FAKE'
    gsheet = get_spreadsheet(client, url)

    assert gsheet['has_cp_export']
    assert gsheet['is_init']
    assert gsheet['worksheets']==worksheets
    assert gsheet['dates']==all_dates
    assert not any(gsheet['date_has_car_group'])
    assert not gsheet['car_group_date_error']
    assert not gsheet['is_complete']


@pytest.mark.parametrize('day', range(1, len(all_dates)+1))
def test_has_cars(monkeypatch, client, day):
    worksheets = [FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, DRIVER_WORKSHEET]
    for k in range(day):
        worksheets.append(CAR_GROUP_WORKSHEET.format(k+1))
    dfs = [df_full_roster, df_roster, df_drivers]
    set_mockreturn(client, monkeypatch, worksheets, dfs)

    url = 'FAKE'
    gsheet = get_spreadsheet(client, url)

    assert gsheet['has_cp_export']
    assert gsheet['is_init']
    assert gsheet['worksheets']==worksheets
    assert gsheet['dates']==all_dates
    assert sum(gsheet['date_has_car_group']) == day
    assert not gsheet['car_group_date_error']
    assert gsheet['is_complete'] == (day==4)
