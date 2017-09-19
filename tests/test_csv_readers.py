from csv_readers import read_csv_file

def test_read_csv_file_regular():
    # Regular test, cutting off 
    filename = "test_data/csv_readers_test_reg.csv"
    expected_regular = [
        {"Field 1": 'A', 'Field 2': 'B', 'Field 3': 'C'},
        {"Field 1": 'D', 'Field 2': 'E', 'Field 3': 'F'},
        {"Field 1": 'H', 'Field 2': 'I', 'Field 3': ''}
        ]
    print("Regular (non-varlen) csv file:", filename)
    result = read_csv_file(filename)
    assert result == expected_regular

    # Trying an empty field name
    emp_field_file = "test_data/csv_readers_test_empfield.csv"
    result = read_csv_file(emp_field_file)
    expected_empfield = [
        {"Field 1": '1', '': '3', 'Field 2': '2', 'field 4': '4'},
        {"Field 1": '1', '': '' ,'Field 2': '2', 'field 4': ''}
        ]
    # print(result)
    # print(expected_empfield)
    # probably would need to create an alias for an empty field
    assert expected_empfield == result

    # Multiple empty fields
    mult_emp_field_file = "test_data/csv_readers_test_mult_empfield.csv"
    result = read_csv_file(mult_emp_field_file)
    expected_mult_empfield = [
        {"Field 1": '1', '': '3', 'Field 2': '2', 'Field 4': '4'},
        {"Field 1": '1', '': '' ,'Field 2': '2', 'Field 4': ''}
        ]
    print(result)
    print(expected_mult_empfield)
    # probably would need to create an alias for an empty field/column name
    assert expected_mult_empfield == result

def test_read_csv_file_varlen():
    # Testing with varlen set to true
    expected_varlen = [
        {"Field 1": 'A', 'Field 2': 'B', 'Selections': ('C', 'G', 'H')},
        {"Field 1": 'D', 'Field 2': 'E', 'Selections': ('F', 'G')},
        {"Field 1": 'H', 'Field 2': 'I', 'Selections': ()}
        ]
    filename = "test_data/csv_readers_test_varlen.csv"
    print("Varlen csv file:", filename)
    result = read_csv_file(filename, varlen = True)
    assert result == expected_varlen

#def test_read_csv_file_varlen():

