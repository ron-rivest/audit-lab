"""
Tests routines for ids.py
"""

import ids

def test_clean_id():

    assert ids.clean_id(" ab") == "ab"
    assert ids.clean_id("ab ") == "ab"
    assert ids.clean_id("  ab cd  ") == "ab cd"
    assert ids.clean_id("\t ab\n cd\n") == "ab cd"


def test_filename_safe():

    assert ids.filename_safe("abc ") == "abc"
    assert ids.filename_safe("ab(c)d*8=_e-f+[g]h/i") == "abcd8_e-f+ghi"


def test_is_writein():

    assert ids.is_writein("abc") == False
    assert ids.is_writein("+abc") == True


def test_is_error_selid():

    assert ids.is_error_selid("abc") == False
    assert ids.is_error_selid("-abc") == True

    
                             
    
