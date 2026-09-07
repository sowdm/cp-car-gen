AFFILIATION_COL = 'Affiliation'
DATES_COL = 'Canvassing Dates'
HALF_DAY_COL = 'Half Day Status'
GENERATION_COL = 'Generation'
EXPERIENCE_COL = 'Canvassing Experience'
BIPOC_COL = 'BIPOC Status'
ORIG_COLS = ['First Name', 'Last Name', 'Will Be A Driver', 'Willing To Be Backup Car', AFFILIATION_COL, DATES_COL, HALF_DAY_COL,
             GENERATION_COL, BIPOC_COL, EXPERIENCE_COL]
NAME_COL = 'Name'
RENAME_COLS = {'Will Be A Driver':'Driver','Willing To Be Backup Car':'Backup Driver','First Name':NAME_COL}
DELETE_COLS =[DATES_COL, 'Last Name']

SAME_CAR = 'Same Car'
DIFFERENT_CAR = 'Different Car'
PAIR_COL = f'{SAME_CAR} / {DIFFERENT_CAR}'
SEPARATE_COL = 'If Same Car, Should This Group Be In Their Own Car?'
NAME1_COL = 'Name1'
NAME2_COL = 'Name2'
DRIVER_TYPE_COL = 'Driver Type (Always/Preferred/Backup/Never)'