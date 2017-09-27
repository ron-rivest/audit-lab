# csv_readers.py
# Ronald L. Rivest and Karim Husayn Karimi
# July 27, 2017
# python3

"""
Code to read the various files that multi.py uses from their CSV formats.
"""

"""
All CSV files have a single header line, giving the column (field) names.

For most (non-varlen) file formats, a data row must have length no longer than the header row,
and missing values are represented as "".

For "varlen" files (files with variable row lengths), it is a little bit 
different: the last header may correspond to 0, 1, 2, or more valuesin a data row.
So the data row may be shorter (by one), equal to, or longer than the header row.
In any case, the values for the last field are *always* compiled into a tuple
(possibly an empty tuple).
The reader returns a list of dictionaries, one per row.
Example (regular csv file):
    A,B,C
    1,2,3
    4,5
becomes:
    [ {'A':'1', 'B':'2', 'C':'3'},
      {'A':'4', 'B':'5', 'C':''} 
    ]
Example: (varlen csv file)
    A,B,C
    1,2,3
    4,5
    6,7,8,9
becomes:
    [ {'A':'1', 'B':'2', 'C':('3',)},
      {'A':'4', 'B':'5', 'C':()},
      {'A':'6', 'B':'7', 'C':('8','9')},
    ]
"""

import csv
import warnings

import ids


def read_csv_file(filename, required_fieldnames=None, varlen=False):
    """
    Read CSV file and check required fieldnames present; varlen if variable-length rows.
    """

    # print("Reading CSV file:", filename)
    with open(filename) as file:
        reader = csv.reader(file)
        rows = [row for row in reader]
        fieldnames = rows[0]
        rows = rows[1:]

        # gather, clean, and trim field names, eliminating blanks
        fieldnames = [ids.clean_id(fieldname) for fieldname in fieldnames]
        while len(fieldnames)>0 and fieldnames[-1]=='':
            fieldnames.pop()
        if len(set(fieldnames)) != len(fieldnames):
            raise ValueError("Duplicate field name: {}".format(fieldnames))

        # data rows
        row_dicts = []
        for row in rows:
            row = ["" if item==None else ids.clean_id(item) for item in row]
            while len(row)>0 and row[-1] == '':
                row.pop()
            if not varlen:
                if len(row) > len(fieldnames):
                    warnings.warn("Ignoring extra values in row: {}".format(row))
                    row = row[:len(fieldnames)]
                while len(row) < len(fieldnames):
                    row.append("")
            row_dict = {}
            for (fieldname, value) in zip(fieldnames, row):
                row_dict[fieldname] = value
            if varlen:
                if len(row) < len(fieldnames)-1:
                    if len(row) > 0:
                        warnings.warn("Ignoring too-short row: {}".format(row))
                    continue
                last_fieldname = fieldnames[-1]
                last_value = tuple(row[len(fieldnames)-1:])
                row_dict[last_fieldname] = last_value
            row_dicts.append(row_dict)
        if required_fieldnames != None:
            # check that all required fieldnames are present
            required_fieldnames = [ids.clean_id(id) for id in required_fieldnames]
            missing_fieldnames = set(required_fieldnames).difference(set(fieldnames))
            if len(missing_fieldnames) > 0:
                raise ValueError("File {} has fieldnames {}, while {} are required. Missing {}."
                                 .format(filename, fieldnames, required_fieldnames, missing_fieldnames))
            # check to see if extra fieldnames present; warn user if so
            extra_fieldnames = set(fieldnames).difference(set(required_fieldnames))
            if len(extra_fieldnames) > 0:
                warnings.warn("File {} has extra fieldnames (ignored): {}"
                              .format(filename, extra_fieldnames))
        return row_dicts

    
