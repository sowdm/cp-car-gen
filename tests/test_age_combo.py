import pandas as pd
import pytest

from cp_cars_generator import combine_age_groups

@pytest.mark.parametrize('num_groups',[1,2,3])
def test_3_or_less_age_groups(num_groups):
    age_cats = [x for x in range(num_groups)]
    s = pd.Series(age_cats)

    s2,new_age_cats = combine_age_groups(s, age_cats)
    assert s.equals(s2)
    assert new_age_cats == age_cats


def test_4_age_groups():
    num_groups = 4
    age_cats = [x for x in range(num_groups)]
    s = pd.Series(age_cats)

    s2,new_age_cats = combine_age_groups(s, age_cats)
    assert new_age_cats == [0,2,3]
    assert s2.tolist()==[0,0,2,3]


def test_5_age_groups():
    num_groups = 5
    age_cats = [x for x in range(num_groups)]
    s = pd.Series(age_cats)

    s2,new_age_cats = combine_age_groups(s, age_cats)
    assert new_age_cats == [0,2,4]
    assert s2.tolist()==[0,0,2,2,4]


def test_6_age_groups():
    num_groups = 6
    age_cats = [x for x in range(num_groups)]
    s = pd.Series(age_cats)

    s2,new_age_cats = combine_age_groups(s, age_cats)
    assert new_age_cats == [0,2,4]
    assert s2.tolist()==[0,0,2,2,4,4]


def test_7_age_groups():
    num_groups = 7
    age_cats = [x for x in range(num_groups)]
    s = pd.Series(age_cats)

    s2,new_age_cats = combine_age_groups(s, age_cats)
    assert new_age_cats == [0,3,5]
    assert s2.tolist()==[0,0,0,3,3,5,5]