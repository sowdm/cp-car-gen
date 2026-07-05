import math
import pytest

import cp_cars_generator

DEFAULT_FULL_CAR_SIZE = cp_cars_generator.FULL_CAR_SIZE
test_full_car_sizes = [4,5]


def get_car_sizes_brute_force(num_vols0, must_be_in_same_car, separate_car, full_car_size):
    # This is intended to be a method that will always work
    carsizes0 = []
    for m,s in zip(must_be_in_same_car, separate_car):
        if len(m)>=full_car_size or s:
            carsizes0.append(len(m))

    num_vols = num_vols0 - sum(carsizes0)

    num_cars = math.ceil(num_vols / full_car_size)
    carsizes = [full_car_size for _ in range(num_cars)]

    for k in range(sum(carsizes) - num_vols):
        carsizes[k % num_cars]-=1

    assert sum(carsizes)==num_vols
    
    carsizes = carsizes0+carsizes
    assert sum(carsizes)==num_vols0
    return carsizes


@pytest.fixture(params=test_full_car_sizes)
def full_car_size(request):
    cp_cars_generator.FULL_CAR_SIZE = request.param
    yield cp_cars_generator.FULL_CAR_SIZE
    cp_cars_generator.FULL_CAR_SIZE = DEFAULT_FULL_CAR_SIZE


@pytest.mark.parametrize('num_vols', range(max(test_full_car_sizes)**2))
def test_basic(num_vols, full_car_size):
    must_be_in_same_car = []
    separate_car = []
    truth = get_car_sizes_brute_force(num_vols, must_be_in_same_car, separate_car, full_car_size)
    carsizes = cp_cars_generator.get_car_sizes(num_vols, must_be_in_same_car, separate_car)
    assert sorted(carsizes) == sorted(truth)

@pytest.mark.parametrize('num_paired', range(1, DEFAULT_FULL_CAR_SIZE))
def test_small_pairing(num_paired):
    num_vols = 9
    must_be_in_same_car = [range(num_paired)]
    separate_car = [False for _ in range(num_paired)]
    truth = get_car_sizes_brute_force(num_vols, must_be_in_same_car, separate_car, DEFAULT_FULL_CAR_SIZE)
    carsizes = cp_cars_generator.get_car_sizes(num_vols, must_be_in_same_car, separate_car)
    assert sorted(carsizes) == sorted(truth)


@pytest.mark.parametrize('num_paired', [DEFAULT_FULL_CAR_SIZE, DEFAULT_FULL_CAR_SIZE+1])
def test_large_pairing(num_paired):
    num_vols = 9
    must_be_in_same_car = [range(num_paired)]
    separate_car = [False for _ in range(num_paired)]
    truth = get_car_sizes_brute_force(num_vols, must_be_in_same_car, separate_car, DEFAULT_FULL_CAR_SIZE)
    carsizes = cp_cars_generator.get_car_sizes(num_vols, must_be_in_same_car, separate_car)
    assert sorted(carsizes) == sorted(truth)


def test_separate_car():
    num_vols = 20
    must_be_in_same_car = [range(5), range(5,10), range(10,12)]
    separate_car = [False, True, True]
    truth = get_car_sizes_brute_force(num_vols, must_be_in_same_car, separate_car, DEFAULT_FULL_CAR_SIZE)
    carsizes = cp_cars_generator.get_car_sizes(num_vols, must_be_in_same_car, separate_car)
    assert sorted(carsizes) == sorted(truth)