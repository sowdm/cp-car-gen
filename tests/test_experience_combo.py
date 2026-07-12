import pandas as pd
import pytest

from cp_cars_generator import combine_experience_groups

EXPERIENCE_CATS = ['None', 'I have done it once or twice without CP', 
                   'I have a lot, but not with CP','I have done it once or twice with CP',
                   'I have a lot, and canvassed with CP']


@pytest.mark.parametrize('day', [1,2])
def test_day1_lots_of_cp_experience(day):
    input = pd.Series([EXPERIENCE_CATS[k] for k in [4,4,4,4,3,2,1,0]])
    out = combine_experience_groups(input, day)

    assert (out[input==EXPERIENCE_CATS[4]]==1).all()
    assert (out[input.isin(EXPERIENCE_CATS[:4])]==0).all()

@pytest.mark.parametrize('day', [1,2])
def test_day1_less_cp_experience(day):
    input = pd.Series([EXPERIENCE_CATS[k] for k in [4,4,4,3,3,2,1,0]])
    out = combine_experience_groups(input, day)

    assert (out[input==EXPERIENCE_CATS[4]]==2).all()
    assert (out[input==EXPERIENCE_CATS[3]]==1).all()
    assert (out[input.isin(EXPERIENCE_CATS[:3])]==0).all()


@pytest.mark.parametrize('day', [1,2])
def test_day1_include_lots_of_canvass_experience(day):
    input = pd.Series([EXPERIENCE_CATS[k] for k in [4,4,3,2,2,2,1,0]])
    out = combine_experience_groups(input, day)

    assert (out[input==EXPERIENCE_CATS[4]]==2).all()
    assert (out[input.isin(EXPERIENCE_CATS[2:4])]==1).all()
    assert (out[input.isin(EXPERIENCE_CATS[:2])]==0).all()


def test_day3():
    day = 3
    input = pd.Series([EXPERIENCE_CATS[k] for k in [4,4,4,4,3,2,1,0]])
    out = combine_experience_groups(input, day)

    assert (out[input.isin(EXPERIENCE_CATS[2:])]==1).all()
    assert (out[input.isin(EXPERIENCE_CATS[:2])]==0).all()

def test_day4():
    day = 4
    input = pd.Series([EXPERIENCE_CATS[k] for k in [4,4,4,4,3,2,1,0]])
    out = combine_experience_groups(input, day)

    assert (out==out[0]).all()