import gspread
import re

import numpy as np
import pandas as pd

from columns import DATES_COL, DELETE_COLS, INIT_PAIRINGS_COLS, ORIG_COLS, RENAME_COLS
from constants import MARK
from worksheets import CAR_GROUP_WORKSHEET, FULL_ROSTER_WORKSHEET, PAIRINGS_WORKSHEET, ROSTER_WORKSHEET, SHEET_INDICATOR


def get_sheet(sht, name):
    worksheet = sht.worksheet(name)
    return pd.DataFrame(worksheet.get_all_records())


def get_spreadsheet(client: gspread.client.Client, url: str):
    sht = client.open_by_url(url)
    worksheet_list = [x.title for x in sht.worksheets() if x.title.startswith(SHEET_INDICATOR)]
    has_cp_export = FULL_ROSTER_WORKSHEET in worksheet_list
    is_init = ROSTER_WORKSHEET in worksheet_list and PAIRINGS_WORKSHEET in worksheet_list

    dts = None
    date_has_car_group = None
    error = False
    if has_cp_export:
        df = get_sheet(sht, FULL_ROSTER_WORKSHEET)
        has_cp_export = 'Canvassing Dates' in df
        if has_cp_export:
            dts = set()
            for x in [re.findall(r'\d{1,2}/\d{1,2}/\d{4}', x) for x in df['Canvassing Dates'].tolist()]:
                dts.update(x)
            dts = list({pd.to_datetime(x) for x in dts})  # In case, multiple formats...
            dts.sort()

            date_has_car_group = [CAR_GROUP_WORKSHEET.format(k+1) in worksheet_list for k in range(len(dts))]
            if any(date_has_car_group):
                # Ensure that there are no gaps in dates with car groups
                start = date_has_car_group.index(True)
                end = len(date_has_car_group)-1-date_has_car_group[::-1].index(True)
                error = not all(date_has_car_group[start:end+1])

    return {'url':url, 'file':sht, 'worksheets':worksheet_list, 'has_cp_export':has_cp_export, 'is_init':is_init,
            'dates':dts,'date_has_car_group':date_has_car_group, 'car_group_date_error':error}


def update_sheet(sht, name, df, worksheet_list):
    if name in worksheet_list:
        worksheet = sht.worksheet(name)
        worksheet.clear()
    else:
        worksheet = sht.add_worksheet(name, rows=0, cols=0)

    data = [[int(x) if isinstance(x, np.int64) else x for x in y] for y in df.values.tolist()]
    worksheet.update([df.columns.values.tolist()] + data)


def init(gsheet):
    sht = gsheet['file']
    worksheet_list = gsheet['worksheets']
    if gsheet['is_init']:
        raise ValueError(f'{ROSTER_WORKSHEET} or {PAIRINGS_WORKSHEET} found. Spreadsheet may have already been initialized. Delete these sheets to enable initialization.')

    assert FULL_ROSTER_WORKSHEET in worksheet_list, f'Worksheet entitled {FULL_ROSTER_WORKSHEET} must exist in spreadsheet and contained roster export from app'

    df_full_roster = get_sheet(sht, FULL_ROSTER_WORKSHEET)
    missing_cols = [x for x in ORIG_COLS if x not in df_full_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {FULL_ROSTER_WORKSHEET}: {missing_cols}'

    df_roster = df_full_roster[ORIG_COLS]
    df_roster = df_roster.rename(columns=RENAME_COLS)
    df_roster['Name'] = df_roster.apply(lambda x: f"{x['Name']} {x['Last Name']}", axis=1)

    dates = df_roster[DATES_COL].tolist()
    dates = [x.strip().split(' ') for x in dates]
    date_set = set()
    for d in dates:
        date_set.update(d)
    all_dates = list(set(pd.to_datetime(x) for x in date_set))
    all_dates.sort()

    day_cols = []
    for k,d in enumerate(all_dates):
        day_cols.append(f'Day {k+1} ({d.strftime('%a')})')
        df_roster[day_cols[-1]] = df_roster[DATES_COL].apply(lambda x: MARK if d in [pd.to_datetime(x) for x in x.strip().split(' ')] else '')

    df_roster = df_roster.drop(columns=DELETE_COLS)

    pairings_cols = INIT_PAIRINGS_COLS.copy()
    pairings_cols.extend(day_cols)
    df_pairings = pd.DataFrame([], columns=pairings_cols)

    update_sheet(sht, ROSTER_WORKSHEET, df_roster, worksheet_list)
    update_sheet(sht, PAIRINGS_WORKSHEET, df_pairings, worksheet_list)


def set_day(mode, worksheet_list, ndays):
    group_created = pd.Series([CAR_GROUP_WORKSHEET.format(k+1) in worksheet_list for k in range(ndays)])

    mode = mode.lower()
    if mode=='next':
        day = group_created[group_created].index[-1]+2 if group_created.any() else 1  # +2 = next day + convert to 1-based
    elif mode=='overwrite':
        assert group_created.any(), 'Car group cannot be overwritten if no car groups have been created'
        day = group_created[group_created].index[-1]+1
    else:
        raise ValueError(f'Unknown day parameter: {day}')

    assert group_created[:day-1].all(), f'Attempting to generate car groups for day {day} but not all car groups have been made before day {day}'
    assert day<=ndays, 'Car group requested for a day beyond the number of days in the trip'
    return day