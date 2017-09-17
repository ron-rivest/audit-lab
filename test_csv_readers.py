import os

from csv_readers import read_csv_file

test_filename = "test_file.csv"

def test_csv_one():
    contents = "A,B,C\n1,2,3\n4,5"
    expected = [
        {'A':'1', 'B':'2', 'C':'3'},
        {'A':'4', 'B':'5', 'C':''}
    ]
    with open(test_filename, "w") as f:
        f.write(contents)
    assert read_csv_file(test_filename) == expected
    os.remove(test_filename)

def test_csv_two():
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
