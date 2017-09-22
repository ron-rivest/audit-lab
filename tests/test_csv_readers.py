import os
import sys
from io import StringIO
from contextlib import redirect_stdout

from csv_readers import read_csv_file

test_filename = "test_file.csv"

def test_csv_len():
    # First sample given in csv_readers.py
    contents = "A,B,C\n1,2,3\n4,5"
    expected = [
        {'A':'1', 'B':'2', 'C':'3'},
        {'A':'4', 'B':'5', 'C':''}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_varlen():
    # Second sample given in csv_readers.py
    contents = "A,B,C\n1,2,3\n4,5\n6,7,8,9"
    with open(test_filename, "w") as f:
        f.write(contents)
    expected = [
        {'A':'1', 'B':'2', 'C':('3',)},
        {'A':'4', 'B':'5', 'C':()},
        {'A':'6', 'B':'7', 'C':('8','9')}
    ]
    assert read_csv_file(test_filename, varlen=True) == expected
    os.remove(test_filename)

def test_csv_oneEntry_len():
    # One header with one entry
    contents = "A\n\n1"
    expected = [
        {'A':''},
        {'A':'1'}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_emptyEntries_len():
    # 5 headers with 2 entries in 1 line
    contents = "A,B,C,D,E\n1,2\n1,2,3,4,5"
    expected = [
        {'A':'1','B':'2','C':'','D':'','E':''},
        {'A':'1','B': '2','C':'3','D':'4','E':'5'}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_extraEntries_len():
    # non-varlen error when more entries than fields
    contents = "A,B\n1,2,3"
    expected = [
        {'A':'1','B':'2'}
    ]
    # expected warning message - "Ignoring extra values in row:0"
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_empty_line_len():
    # 5 headers with no entries
    contents = "A,B,C,D,E\n\n1,2,3,4,5"
    expected = [
        {'A':'','B': '','C':'','D':'','E':''},
        {'A':'1','B': '2','C':'3','D':'4','E':'5'}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_tooShortRow_varlen():
    contents = "A,B,C\n1\n1,2,3"
    expected = [
        {'A':'1','B':'2','C':'3'}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)

    f = StringIO()
    with redirect_stdout(f):
        try:
            read_csv_file(test_filename, varlen=True)
        except SystemExit:
            pass
    s = f.getvalue()

    lines = [
        "WARNING: Ignoring too-short row:{}\n".format(['1'])
    ]
    assert s == "\n".join(lines)
    os.remove(test_filename)

def test_csv_longTuple_varlen():
    # Testing the tupling of the last elements if longer than header
    # Note: Documentation for varlen tuples, inside the tuples should be STRING, not INT
    contents = "A,B,C\n1,2,3\n4,5\n6,7,8,9,10,11,12,13,14,15"
    expected = [
        {'A':'1', 'B':'2', 'C':('3',)},
        {'A':'4', 'B':'5', 'C':()},
        {'A': '6', 'B': '7', 'C': ('8', '9', '10', '11', '12', '13', '14', '15')}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename, varlen=True) == expected
    os.remove(test_filename)

def test_csv_required_fieldname_missing():
    # required file name test
    contents = "A,B,C\n1,2,3\n4,5"
    fieldnames = ["A","B","C"]
    missing_fieldnames = set(["D"])
    required_fieldnames = ['A','B','C','D']

    with open(test_filename, "w") as f:
        f.write(contents)

    f = StringIO()
    with redirect_stdout(f):
        try:
            read_csv_file(test_filename, required_fieldnames=required_fieldnames)
        except SystemExit:
            pass
    s = f.getvalue()

    lines = [
        "FATAL ERROR: File {} has fieldnames {}, while {} are required. Missing {}.\n".format(
            test_filename, fieldnames, required_fieldnames, missing_fieldnames)
    ]
    assert s == "\n".join(lines)
    os.remove(test_filename)

def test_csv_extra_required_fieldname():
    # required file name test
    contents = "A,B,C\n1,2,3\n4,5"
    fieldnames = ["A","B","C"]
    extra_fieldnames = set(["C"])

    with open(test_filename, 'w') as f:
        f.write(contents)

    f = StringIO()
    with redirect_stdout(f):
        try:
            read_csv_file(test_filename, required_fieldnames=['A','B'])
        except SystemExit:
            pass
    s = f.getvalue()

    lines = [
        "WARNING: File {} has extra fieldnames (ignored): {}\n".format(test_filename, extra_fieldnames)
    ]
    assert s == "\n".join(lines)
    os.remove(test_filename)

def test_csv_duplicate_field():
    contents = "A,B,B\n1,2,3\n4,5"
    with open(test_filename, 'w') as f:
        f.write(contents)

    f = StringIO()
    with redirect_stdout(f):
        try:
            read_csv_file(test_filename)
        except SystemExit:
            pass
    s = f.getvalue()

    lines = [
        "FATAL ERROR: Duplicate field name:{}\n".format(['A', 'B', 'B'])
    ]
    assert s == "\n".join(lines)
    os.remove(test_filename)
