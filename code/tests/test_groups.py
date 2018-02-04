""" test_groups.py: 
    test the implementation of "contest groups" in 'multi' 
    (as implemented in groups.py)
"""

import multi
import groups
import warnings

def graph_1(e):

    e.gids = [1, 2, 3, 4, 5, 6, 7]
    e.cids = [11, 22, 33, 44, 55, 66, 77]
    e.cgids_g[1] = [11, 2]
    e.cgids_g[2] = [22, 3, 4]
    e.cgids_g[3] = [33]
    e.cgids_g[4] = [44, 5]
    e.cgids_g[5] = [55, 4]
    e.cgids_g[6] = [66, 1, 7]
    e.cgids_g[7] = [77, 3]

def test_expand_contest_group_defs():

    e = multi.Election()
    graph_1(e)

    with warnings.catch_warnings(record=True) as w:
        groups.expand_contest_group_defs(e)
        assert len(w) == 2
        assert str(w[0].message) == 'Group id 4 is in a cycle!'
        assert str(w[1].message) == 'Group id 5 is in a cycle!'

    assert e.cids_g[1] == [11, 22, 33, 44, 55]
    assert e.cids_g[2] == [22, 33, 44, 55]
    assert e.cids_g[3] == [33]
    assert e.cids_g[4] == [44, 55]
    assert e.cids_g[5] == [55, 44]
    assert e.cids_g[6] == [66, 11, 22, 33, 44, 55, 77]
    assert e.cids_g[7] == [77, 33]


def graph_2(e):

    e.gids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    e.cids = [110, 220, 330, 440, 550, 660, 770, 880, 990, 10100, 11110, 12120]
    e.cgids_g[1] = [110, 2, 5, 6]
    e.cgids_g[2] = [220, 3, 11, 12]
    e.cgids_g[3] = [330, 4, 9, 10]
    e.cgids_g[4] = [440, 1, 7, 8]
    e.cgids_g[5] = [550]
    e.cgids_g[6] = [660]
    e.cgids_g[7] = [770]
    e.cgids_g[8] = [880]
    e.cgids_g[9] = [990]
    e.cgids_g[10] = [10100]
    e.cgids_g[11] = [11110]
    e.cgids_g[12] = [12120]


def test_expand_contest_groups_defs_2():

    e = multi.Election()
    graph_2(e)

    with warnings.catch_warnings(record=True) as w:
        groups.expand_contest_group_defs(e)
        assert len(w) == 4
        assert str(w[0].message) == 'Group id 1 is in a cycle!'
        assert str(w[1].message) == 'Group id 2 is in a cycle!'
        assert str(w[2].message) == 'Group id 3 is in a cycle!'
        assert str(w[3].message) == 'Group id 4 is in a cycle!'

    assert e.cids_g[1] == [110, 220, 330, 440, 770, 880, 990, 10100, 11110, 12120, 550, 660]
    assert e.cids_g[2] == [220, 330, 440, 110, 550, 660, 770, 880, 990, 10100, 11110, 12120]
    assert e.cids_g[3] == [330, 440, 110, 220, 11110, 12120, 550, 660, 770, 880, 990, 10100]
    assert e.cids_g[4] == [440, 110, 220, 330, 990, 10100, 11110, 12120, 550, 660, 770, 880]
    assert e.cids_g[5] == [550]
    assert e.cids_g[6] == [660]
    assert e.cids_g[7] == [770]
    assert e.cids_g[8] == [880]
    assert e.cids_g[9] == [990]
    assert e.cids_g[10] == [10100]
    assert e.cids_g[11] == [11110]
    assert e.cids_g[12] == [12120]


def test_expand_gids_in_list():

    e = multi.Election()
    graph_1(e)

    with warnings.catch_warnings(record=True) as w:
        groups.expand_contest_group_defs(e)
        assert len(w) == 2
        assert str(w[0].message) == 'Group id 4 is in a cycle!'
        assert str(w[1].message) == 'Group id 5 is in a cycle!'

    assert groups.expand_gids_in_list(e, [1, 22, 3, 4, 55, 66]) \
        == [11, 22, 33, 44, 55, 22, 33, 44, 55, 55, 66]
