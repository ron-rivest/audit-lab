"""
Tests for outcomes.py
"""
import outcomes


def test_compute_tally():
    """
    Here vec is an iterable of hashable elements.
    Return dict giving tally of elements.
    """
    int_list = [1,2,2,1,1,3]
    expected_int_tally = {1:3,2:2,3:1}
    str_list = ["a", "b","b","a","a","c"]
    expected_str_tally = {"a": 3, "b": 2, "c": 1}

    approval_int_list = [(1, 2, 3, 4), (1, 3), (), (1, 3), (4, 1)]
    expected_int_approval_tally = {(1, 2, 3, 4):1,(1, 3):2,():1,(4, 1):1}
    approval_str_list = [("a", "b", "c", "d"), ("a", "c"), (), ("a", "c"), ("a","d")]
    expected_str_approval_tally = {("a", "b", "c", "d"): 1, ("a", "c"): 2, (): 1, ("a","d"): 1}

    assert(outcomes.compute_tally(int_list)==expected_int_tally)
    assert(outcomes.compute_tally(str_list)==expected_str_tally)
    assert(outcomes.compute_tally(approval_int_list)==expected_int_approval_tally)
    assert(outcomes.compute_tally(approval_str_list)==expected_str_approval_tally)


def test_compute_tally2():
    """
    Here vec is an iterable of hashable elements.
    Return dict giving tally of elements.
    """
    int_tuple_list = [(1,2),(2,2),(2,2),(1,1),(1,1),(3,3)]
    expected_int_result = {(1,2):1,(2,2):2, (1,1):2,(3,3):1}
    str_tuple_list = [("a","b"),("b","b"),("b","b"),("a","a"),("a","a"),("c","c")]
    expected_str_result = {('c', 'c'): 1, ('a', 'b'): 1, ('a', 'a'): 2, ('b', 'b'): 2}

    assert(outcomes.compute_tally(int_tuple_list)==expected_int_result)
    assert(outcomes.compute_tally(str_tuple_list)==expected_str_result)

def test_plurality():
    alice_win_tally = {("Alice",):558.97,("Bob",):543.01422}
    assert(("Alice",)==outcomes.plurality(None, None,alice_win_tally))
    bob_win_tally = {('Alice',): 1.0, ('Bob',): 5.0}
    assert(('Bob',)==outcomes.plurality(None, None,bob_win_tally))



def test_approval():
    str_tally = {("Alice", "Bob", "Charlie", "David"): 1, ("Alice", "Charlie"): 2, (): 1, ("Alice","David"): 1}
    expected_str_winner = ("Alice",)
    assert(expected_str_winner==outcomes.approval(None, None,str_tally))
