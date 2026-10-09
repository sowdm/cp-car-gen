import gspread
import re

import numpy as np
import pandas as pd

import columns
from columns import DATES_COL, DELETE_COLS, ORIG_COLS, RENAME_COLS, NAME_COL, DRIVER_TYPE_COL
import constants
import utils
from worksheets import CAR_GROUP_WORKSHEET, FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, SHEET_INDICATOR, DRIVER_WORKSHEET, TRIP_STATS_WORKSHEET


def get_sheet(sht, name, clean=False, str_cols=[], name_cols=[], numeric_cols=[]):
    worksheet = sht.worksheet(name)
    records = worksheet.get_all_records()
    if len(records)>0:
        df = pd.DataFrame(records)
    else:
        cols = worksheet.row_values(1)
        df = pd.DataFrame(columns=cols)

    if clean:
        df = utils.clean_df(df, str_cols=str_cols, name_cols=name_cols, numeric_cols=numeric_cols)

    return df


def get_spreadsheet(client: gspread.client.Client, url: str):
    sht = client.open_by_url(url)
    worksheet_list = [x.title for x in sht.worksheets() if x.title.startswith(SHEET_INDICATOR)]
    has_cp_export = FULL_ROSTER_WORKSHEET in worksheet_list
    is_init = ROSTER_WORKSHEET in worksheet_list and DRIVER_WORKSHEET in worksheet_list and TRIP_STATS_WORKSHEET in worksheet_list

    df = None
    dts = None
    date_has_car_group = None
    error = False
    is_complete = False
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
                error = not date_has_car_group[0] and any(date_has_car_group)
                if not error:
                    false_found = False
                    for has_car_group in date_has_car_group:
                        if false_found and has_car_group:
                            error = True
                            break
                        elif not has_car_group:
                            false_found = True

                is_complete = all(date_has_car_group)

    return {'url':url, 'file':sht, 'worksheets':worksheet_list, 'has_cp_export':has_cp_export, 'is_init':is_init,
            'dates':dts,'date_has_car_group':date_has_car_group, 'car_group_date_error':error,
            'is_complete':is_complete, 'df_roster_raw':df}


def update_sheet(sht, name, df, worksheet_list, color=None, index=None, row=1, clear=True):
    if name in worksheet_list:
        worksheet = sht.worksheet(name)
        if clear:
            worksheet.clear()
    else:
        worksheet = sht.add_worksheet(name, rows=0, cols=0, index=index)

    df = df.apply(lambda x: x.apply(lambda y: 'X' if isinstance(y, (bool, np.bool)) and y else y))  
    df = df.apply(lambda x: x.apply(lambda y: '' if isinstance(y, (bool, np.bool)) and not y else y))  
    df = df.fillna(0)

    data = [[int(x) if isinstance(x, np.int64) else x for x in y] for y in df.values.tolist()]
    # nrows = len(df)
    # ncols = len(df.columns)
    my_range = f'A{row}'  #:{chr(64+ncols)}{row+nrows}'
    worksheet.update(range_name=my_range, values=[df.columns.values.tolist()] + data)

    if color:
        worksheet.update_tab_color(color)


def init(gsheet):
    sht = gsheet['file']
    worksheet_list = gsheet['worksheets']

    assert FULL_ROSTER_WORKSHEET in worksheet_list, f'Worksheet entitled {FULL_ROSTER_WORKSHEET} must exist in spreadsheet and contained roster export from app'

    df_full_roster = gsheet['df_roster_raw']
    missing_cols = [x for x in ORIG_COLS if x not in df_full_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {FULL_ROSTER_WORKSHEET}: {missing_cols}'

    df_roster = df_full_roster[ORIG_COLS]
    df_roster = df_roster.rename(columns=RENAME_COLS)
    df_roster[NAME_COL] = df_roster.apply(lambda x: f"{x[NAME_COL]} {x['Last Name']}", axis=1)

    dates = df_roster[DATES_COL].tolist()
    dates = [x.strip().split() for x in dates]
    date_set = set()
    for d in dates:
        date_set.update(d)
    all_dates = list(set(pd.to_datetime(x) for x in date_set))
    all_dates.sort()

    day_cols = []
    for k,d in enumerate(all_dates):
        day_cols.append(f'Day {k+1} ({d.strftime('%a')})')
        df_roster[day_cols[-1]] = df_roster[DATES_COL].apply(lambda x: constants.MARK if d in [pd.to_datetime(x) for x in x.strip().split()] else '')

    df_roster = df_roster.drop(columns=DELETE_COLS)

    drivers = {NAME_COL:[], DRIVER_TYPE_COL:[]}
    for d in day_cols:
        drivers[d] = []
    for k in df_roster.index:
        is_driver = True
        if df_roster.loc[k, 'Driver'].lower()=='yes':
            if df_roster.loc[k, 'Will Have Car On The Ground'].lower()=='yes':
                drivers[DRIVER_TYPE_COL].append(5)
            else:
                drivers[DRIVER_TYPE_COL].append(4)
        elif df_roster.loc[k, 'Backup Driver'].lower()=='yes':
            if df_roster.loc[k, 'Will Have Car On The Ground'].lower()=='yes':
                drivers[DRIVER_TYPE_COL].append(3)
            else:
                drivers[DRIVER_TYPE_COL].append(1)
        elif df_roster.loc[k, 'Will Have Car On The Ground'].lower()=='yes':
            drivers[DRIVER_TYPE_COL].append(2)
        else:
            is_driver = False

        if is_driver:
            drivers[NAME_COL].append(df_roster.loc[k, NAME_COL])
            for d in day_cols:
                drivers[d].append(df_roster.loc[k, d])

    df_drivers = pd.DataFrame(drivers)

    update_sheet(sht, ROSTER_WORKSHEET, df_roster, worksheet_list)
    update_sheet(sht, DRIVER_WORKSHEET, df_drivers, worksheet_list)

    df_roster = get_sheet(gsheet['file'], ROSTER_WORKSHEET, clean=True, 
                    str_cols=[columns.HALF_DAY_COL, columns.GENERATION_COL, columns.EXPERIENCE_COL, columns.AFFILIATION_COL,
                                'MiniVan Experience', 'Dietary Restrictions'],
                    name_cols=[NAME_COL])
    
    no_name = df_roster[NAME_COL].apply(lambda x: len(x.strip())==0)
    no_name = no_name[no_name]
    num_unnamed = 0
    for k in no_name.index:
        num_unnamed+=1
        df_roster.loc[k, NAME_COL] = f'UNNAMED {num_unnamed}'

    update_trip_stats(df_roster, day_cols, sht, worksheet_list)


def update_trip_stats(df_roster, day_cols, sht, worksheet_list):
    df = pd.DataFrame(columns=['Volunteers','Capacity (Drivers x 4)','Not Enough Drivers Warning!', 'Drivers', 
                            'Backup Drivers', 'BIPOC Status'], index=day_cols)
    df['Volunteers'] = df_roster[day_cols].sum()

    for c in day_cols:
        df.loc[c, 'Drivers'] = df_roster['Driver'][df_roster[c]].sum()
        df.loc[c, 'Capacity (Drivers x 4)'] = df.loc[c, 'Drivers'] * 4
        df.loc[c, 'Not Enough Drivers Warning!'] = df.loc[c, 'Capacity (Drivers x 4)'] < df.loc[c, 'Volunteers']
        df.loc[c, 'Backup Drivers'] = df_roster['Backup Driver'][df_roster[c]].sum()
        df.loc[c, 'BIPOC Status'] = df_roster['BIPOC Status'][df_roster[c]].sum()

    update_sheet(sht, TRIP_STATS_WORKSHEET, df.reset_index(names=''), worksheet_list)
    nrows = len(df)+3
    worksheet_list.append(TRIP_STATS_WORKSHEET)

    generations = df_roster['Generation'].unique()
    df = pd.DataFrame(columns=generations, index=day_cols)

    for c in day_cols:
        df.loc[c, : ] = df_roster[df_roster[c]]['Generation'].value_counts()

    update_sheet(sht, TRIP_STATS_WORKSHEET, df.reset_index(names=''), worksheet_list, row=nrows, clear=False)
    nrows += len(df)+2

    exp = df_roster['Canvassing Experience'].unique()
    df = pd.DataFrame(columns=exp, index=day_cols)

    for c in day_cols:
        df.loc[c, : ] = df_roster[df_roster[c]]['Canvassing Experience'].value_counts()

    update_sheet(sht, TRIP_STATS_WORKSHEET, df.reset_index(names=''), worksheet_list, row=nrows, clear=False)
    nrows += len(df)+2

    diets = df_roster['Dietary Restrictions'].unique()
    df = pd.DataFrame(columns=diets, index=day_cols)

    for c in day_cols:
        df.loc[c, : ] = df_roster[df_roster[c]]['Dietary Restrictions'].value_counts()

    df = df.drop(columns=['','No','None'], errors='ignore')

    update_sheet(sht, TRIP_STATS_WORKSHEET, df.reset_index(names=''), worksheet_list, row=nrows, clear=False)


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

def load_url(client, url, reinit=False):
    url = url.strip()
    try:
        gsheet = get_spreadsheet(client, url)
    except PermissionError:
        errmsg = 'The entered URL has not been shared with this app. Please follow the instructions below for sharing your Google spreadsheet.'
        return None, errmsg
        
    errmsg = None
    if not gsheet['has_cp_export']:
        errmsg = f'Spreadsheet does not have tab called "{FULL_ROSTER_WORKSHEET}" containing the roster' +\
                ' from the app. Please follow the instructions below for setting up your Google spreadsheet.'
    elif not gsheet['is_init'] or reinit:
        try:
            init(gsheet)
            gsheet = get_spreadsheet(client, url)
        except gspread.exceptions.APIError as e:
            if len(e.args)>0 and 'message' in e.args[0] and 'A tab with the name' in e.args[0]['message'] and \
                 'already exists' in e.args[0]['message']:
                raise e
            errmsg = 'The entered URL is not shared with Editor access. Please follow the instructions below for setting up your Google spreadsheet. ' \
                'If you have set access properly, try loading the spreadsheet again.'

    return gsheet, errmsg