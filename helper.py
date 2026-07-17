import gspread
import pandas as pd
import re

from worksheets import ROSTER_WORKSHEET, PAIRINGS_WORKSHEET, FULL_ROSTER_WORKSHEET, CAR_GROUP_WORKSHEET

def get_sheet(sht, name):
    worksheet = sht.worksheet(name)
    return pd.DataFrame(worksheet.get_all_records())

def get_spreadsheet(client: gspread.client.Client, url: str):
    sht = client.open_by_url(url)
    worksheet_list = [x.title for x in sht.worksheets()]
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
