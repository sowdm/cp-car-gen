DATES_COL = 'Canvassing Dates'
ORIG_COLS = ['First Name', 'Last Name', 'Will Be A Driver', 'Willing To Be Backup Car', DATES_COL, 'Half Day Status',
             'Generation', 'BIPOC Status', 'Canvassing Experience']
RENAME_COLS = {'Will Be A Driver':'Driver','Willing To Be Backup Car':'Backup Driver','First Name':'Name'}
DELETE_COLS =[DATES_COL, 'Last Name']

PAIR_COL = 'Pair (Yes/No)'
SEPARATE_COL = 'Separate Car'
NAME1_COL = 'Name1'
NAME2_COL = 'Name2'
INIT_PAIRINGS_COLS = [NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL]