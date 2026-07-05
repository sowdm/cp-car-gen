import pandas as pd
import pytest

from cp_cars_generator import get_pairs, NAME1_COL, NAME2_COL, PAIR_COL, SEPARATE_COL, MARK

def test_pair():
    d = {NAME1_COL: ['A'], NAME2_COL: ['B'], PAIR_COL:['yes'], SEPARATE_COL:['']}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert must_pair==[set(['A','B'])]
    assert separate_car==[False]
    assert do_not_pair==[]

def test_do_not_pair():
    d = {NAME1_COL: ['A'], NAME2_COL: ['B'], PAIR_COL:['no'], SEPARATE_COL:['']}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert do_not_pair==[set(['A','B'])]
    assert must_pair==[]
    assert separate_car==[]

def test_complex_pair():
    d = {NAME1_COL: ['A','C','E','B'], NAME2_COL: ['B','D','F','E'], PAIR_COL:['yes','yes','yes','yes'], SEPARATE_COL:['','','','']}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert must_pair==[set(['A','B','E','F']), set(['C','D'])]
    assert separate_car==[False, False]
    assert do_not_pair==[]

def test_mixed():
    d = {NAME1_COL: ['A','C','E','B','G','I','G'], NAME2_COL: ['B','D','F','E','H','J','J'], PAIR_COL:['yes','yes','yes','yes','no','no','no'],
         SEPARATE_COL:['','','','','','','']}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert must_pair==[set(['A','B','E','F']), set(['C','D'])]
    assert separate_car==[False, False]
    assert do_not_pair==[set(['G','H','I','J'])]

def test_conflict():
    d = {NAME1_COL: ['A','A'], NAME2_COL: ['B','B'], PAIR_COL:['yes','no'], SEPARATE_COL:['','']}
    df = pd.DataFrame(data=d)

    with pytest.raises(AssertionError):
        get_pairs(df)


@pytest.mark.parametrize('mark', [MARK, MARK.lower()])
def test_separate_car_pair(mark):
    d = {NAME1_COL: ['A'], NAME2_COL: ['B'], PAIR_COL:['yes'], SEPARATE_COL:[mark]}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert must_pair==[set(['A','B'])]
    assert separate_car==[True]
    assert do_not_pair==[]


@pytest.mark.parametrize('mark', [MARK, MARK.lower()])
def test_separate_car_do_not_pair(mark):
    d = {NAME1_COL: ['A'], NAME2_COL: ['B'], PAIR_COL:['no'], SEPARATE_COL:[mark]}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert do_not_pair==[set(['A','B'])]
    assert must_pair==[]
    assert separate_car==[]


@pytest.mark.parametrize('loc', [0, 2, 3])
def test_separate_car_complex_pair(loc):
    separate = ['','','','']
    separate[loc] = MARK
    d = {NAME1_COL: ['A','C','E','B'], NAME2_COL: ['B','D','F','E'], PAIR_COL:['yes','yes','yes','yes'], SEPARATE_COL:separate}
    df = pd.DataFrame(data=d)

    must_pair, separate_car, do_not_pair = get_pairs(df)
    assert must_pair==[set(['A','B','E','F']), set(['C','D'])]
    assert separate_car==[True, False]
    assert do_not_pair==[]