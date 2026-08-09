import argparse
import gspread
import numpy as np
import pandas as pd
import re
import tomllib

import cp_gsheet
from worksheets import FULL_ROSTER_WORKSHEET, ROSTER_WORKSHEET, PAIRINGS_WORKSHEET, CAR_GROUP_WORKSHEET
import generator
from columns import ORIG_COLS, RENAME_COLS, DATES_COL, DELETE_COLS, INIT_PAIRINGS_COLS, NAME1_COL, NAME2_COL
from constants import MARK

# TODO: Test that optimization has predicted results for simple weights

with open('.streamlit/secrets.toml', 'rb') as f:
    secrets = tomllib.load(f)
URL = secrets['SAMPLE_URL']

with open('config.toml') as f:
    config = tomllib.load(f)

pairings_cols = INIT_PAIRINGS_COLS.copy()
roster_cols = [RENAME_COLS[x] if x in RENAME_COLS else x for x in ORIG_COLS if x not in DELETE_COLS]


def init():
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')

    data = cp_gsheet.get_spreadsheet(gc, URL)
    sht = data['spreadsheet']
    worksheet_list = data['worksheets']
    if data['is_init']:
        raise ValueError(f'{ROSTER_WORKSHEET} or {PAIRINGS_WORKSHEET} found. Spreadsheet may have already been initialized. Delete these sheets to enable initialization.')

    assert FULL_ROSTER_WORKSHEET in worksheet_list, f'Worksheet entitled {FULL_ROSTER_WORKSHEET} must exist in spreadsheet and contained roster export from app'

    df_full_roster = cp_gsheet.get_sheet(sht, FULL_ROSTER_WORKSHEET)
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

    pairings_cols.extend(day_cols)
    df_pairings = pd.DataFrame([], columns=pairings_cols)

    cp_gsheet.update_sheet(sht, ROSTER_WORKSHEET, df_roster, worksheet_list)
    cp_gsheet.update_sheet(sht, PAIRINGS_WORKSHEET, df_pairings, worksheet_list)

def main(mode):
    gc = gspread.service_account(filename=r'streamlit/common-power-6502fad9d9f3.json')
    data = cp_gsheet.get_spreadsheet(gc, URL)
    sht = data['file']
    worksheet_list = data['worksheets']
    assert data['is_init'], f'Spreadsheet must be initialized. init (-i) must be run'

    df_roster = cp_gsheet.get_sheet(sht, ROSTER_WORKSHEET)
    df_pairings = cp_gsheet.get_sheet(sht, PAIRINGS_WORKSHEET)

    day_cols = [x for x in df_roster.columns if re.search(r'^Day\s\d+\s', x)]

    missing_cols = [x for x in roster_cols if x not in df_roster]
    assert len(missing_cols)==0, f'Expected columns are missing from {ROSTER_WORKSHEET}: {missing_cols}'
    pairings_cols.extend(day_cols)
    missing_cols = [x for x in pairings_cols if x not in df_pairings]
    assert len(missing_cols)==0, f'Expected columns are missing from {PAIRINGS_WORKSHEET}: {missing_cols}'

    ndays = len(day_cols)
    day = cp_gsheet.set_day(mode, worksheet_list, ndays)

    day_col = [x for x in df_roster.columns if x.startswith(f'Day {day}')][0]
    df_roster = df_roster[df_roster[day_col].str.lower()==MARK.lower()].reset_index(drop=True)
    df_pairings = df_pairings[df_pairings[day_col].str.lower()==MARK.lower()].reset_index(drop=True)
    df_pairings = df_pairings[df_pairings[NAME1_COL].isin(df_roster['Name']) & df_pairings[NAME2_COL].isin(df_roster['Name'])]

    df_out = generator.gen_car_groups(df_roster, df_pairings, day, sht)

    # TODO: Resort sheets so that highest priority are on the left???
    # TODO: Add key sheet that tells what each sheet is including what ! is???
    # TODO: In app, include ability to modify pairings

    # sheet = DETAILED_CAR_GROUP_WORKSHEET.format(day)
    # helper.update_sheet(sht, sheet, df_out.reset_index(), worksheet_list)

    sheet = CAR_GROUP_WORKSHEET.format(day)
    df_out_min = df_out[[x for x in df_out.columns if x.startswith('Car')]].reset_index()
    cols = list(df_out_min.columns)
    cols[0] = ''
    df_out_min.columns = cols
    cp_gsheet.update_sheet(sht, sheet, df_out_min, worksheet_list)


def find_group(req_group0, vols, group):
    for k in vols:
        cur_group = set(np.setdiff1d(req_group0[:,k].nonzero(),k))
        cur_group = cur_group - group
        group.add(k)

        group = find_group(req_group0, cur_group, group)

    return group

def _get_rem(num_vols):
    return (config['FULL_CAR_SIZE'] - (num_vols % config['FULL_CAR_SIZE']) ) % config['FULL_CAR_SIZE']

def get_num_cars(num_vols):
    # # of carsize-1 cars + # of carsize cars
    rem = _get_rem(num_vols)
    return int(rem + (num_vols-rem*(config['FULL_CAR_SIZE']-1)) / config['FULL_CAR_SIZE'])

def groupname(day):
    return f"CarGroup{day}"

if __name__=='__main__':
    parser = argparse.ArgumentParser(
                    prog='CP Cars Generator',
                    description='Populates Google Sheet with Car Groups Based on Optimization')
    parser.add_argument('-i', '--init', action='store_true', help='Spreadsheet must be initialized before use.') 
    parser.add_argument('-m', '--mode', default='next', choices=['next','overwrite'], help='Generate car group for next day or overwrite most recent day')

    args = parser.parse_args()

    if args.init:
        init()
    else:
        main(args.mode)
    
    # filename = 'volunteers.xlsx'

    # if not os.path.exists(filename):
    #     df_all = sim_volunteers(20)
    #     df_all.to_excel(filename, index=False)

    # gen_car_groups(filename)