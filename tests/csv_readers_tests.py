# tests for csv_readers.py
import csv
import unittest
import sys
sys.path.append("../")

import csv_readers

# function to create csv files
def create_csv(input):
    with open("example.csv", "w") as f:
        writer = csv.writer(f, lineterminator = '\n')
        writer.writerows(input) 

class CSVreaders(unittest.TestCase):

    # testing most simple case
    def test_csv_base(self):
        to_in = [["A", "B", "C"], [1, 2, 3]]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv"), [{'A': '1', 'B': '2', 'C': '3'}])

    # testing if blank cells exist
    def test_csv_blank(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [4, 5, '']]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv"), [{'A': '1', 'B': '2', 'C': '3'}, {'A': '4', 'B': '5', 'C': ''}])

    # testing varlen functionality
    def test_csv_varlen(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [4, 5, ''], [6, 7, 8, 9]]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv", varlen=True), [{'A': '1', 'B': '2', 'C': ('3',)}, 
                                                                                    {'A': '4', 'B': '5', 'C': ()},
                                                                                    {'A': '6', 'B': '7', 'C': ('8','9')}])
    
    # testing varlen functionality for extended length last column
    def test_csv_varlen2(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [4, 5, '', '', ''], [6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 20, 21, 243, 80]]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv", varlen=True), [{'A': '1', 'B': '2', 'C': ('3',)}, 
                                                                                 {'A': '4', 'B': '5', 'C': ()},
                                                                                 {'A': '6', 'B': '7', 'C': 
                                                                                        ('8','9','10','11','12','13','17','18','20','21','243','80')}])

    # testing extra fieldnames beyond required
    def test_csv_extra_fieldnames1(self):
        to_in = [["A", "B", "C", "D"], [1, 2, 3, 4], [6, 7, 8, 8]]
        create_csv(to_in)
        self.assertWarnsRegex(UserWarning, "extra fieldnames", csv_readers.read_csv_file, "example.csv", required_fieldnames=["A","B","C"])
        self.assertEqual(csv_readers.read_csv_file("example.csv", required_fieldnames=["A", "B", "C"]), [{'A': '1', 'B': '2', 'C': '3', 'D': '4'}, {'A': '6', 'B': '7', 'C': '8','D': '8'}])

    # testing above but for variable length
    def test_csv_extra_fieldnames2(self):
        to_in = [["A", "B", "C", "D"], [1, 2, 3, 4], [6, 7, 8, ], [3, 4, 5, 6, 2, 4]]
        create_csv(to_in)
        self.assertWarnsRegex(UserWarning, "extra fieldnames", csv_readers.read_csv_file, "example.csv", varlen=True, required_fieldnames=["C", "B"])
        self.assertEqual(csv_readers.read_csv_file("example.csv", varlen=True, required_fieldnames=["C","B"]), [{'A': '1', 'B': '2', 'C': '3', 'D': ('4',)}, {'A': '6', 'B': '7', 'C': '8', 'D': ()}, {'A': '3', 'B': '4', 'C': '5', 'D': ('6', '2', '4')}])

    # testing if one or more required fieldnames are missing
    def test_csv_required_fieldnames(self):
        to_in = [["A", "B", "C", "D"], [1, 2, 3, 4], [6, 7, 8, 8]]
        create_csv(to_in)
        self.assertRaisesRegex(Exception, 'Missing', csv_readers.read_csv_file, "example.csv", required_fieldnames=["A", "B", "E"])

    # testing for duplicate column names
    def test_csv_duplicate(self):
        to_in = [["A", "B", "C", "D", "D"], [1, 2, 3, 4, 5], [6, 7, 8, 8, 8], ['', '', '', '', '']]
        create_csv(to_in)
        self.assertRaisesRegex(Exception, 'Duplicate', csv_readers.read_csv_file, "example.csv")

    # testing if varlen is false and there are too many values
    def test_csv_varlen_unspecified(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [4, 5, ''], [6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 20, 21, 243, 80]]
        create_csv(to_in)
        self.assertWarnsRegex(UserWarning, 'extra values', csv_readers.read_csv_file, "example.csv")
        self.assertEqual(csv_readers.read_csv_file("example.csv"), [{'A': '1', 'B': '2', 'C': '3'}, {'A': '4', 'B': '5', 'C': ''}, {'A': '6', 'B': '7', 'C': '8'}])

    # testing if varlen is true and there are not enough values
    def test_csv_varlen_true(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [4, 5, ''], []]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv", varlen=True), [{'A': '1', 'B': '2', 'C': ('3', )}, {'A': '4', 'B': '5', 'C': ()}])

    # testing if varlen is true and there is an empty row sandwiched between two valid rows
    def test_csv_varlen_true_blank_row(self):
        to_in = [["A", "B", "C"], [1, 2, 3], [], [4, 5, 6]]
        create_csv(to_in)
        self.assertEqual(csv_readers.read_csv_file("example.csv", varlen=True), [{'A': '1', 'B': '2', 'C': ('3', )}, {'A': '4', 'B': '5', 'C': ('6', )}])


if __name__=="__main__":
    unittest.main()



