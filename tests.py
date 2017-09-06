def test_evens():
    for i in range(5):
        yield check_even, i, i * 2

def check_even(n, nn):
    assert n % 2 == 0 or nn % 2 == 0

def check_var():
    import os
    assert os.getenv("TEST_VAR") == 1
