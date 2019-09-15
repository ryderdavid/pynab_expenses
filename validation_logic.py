#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ryder Cobean
CS 521
Final Project - Expenses Tracker
Created on Wed Jul 31

@author: ryder
"""

import os


def get_file(extension):
    """Simple function for collecting a filename from input."""

    get_file_prompt = '\nEnter valid {} file:\n>> '.format(extension)

    file_ret = str(input(get_file_prompt))

    while True:
        if not os.path.exists(file_ret):
            print('Couldn\'t find {}. Try another file?'.format(file_ret))
            file_ret = str(input(get_file_prompt))
        elif not file_ret.split('.')[-1] == '{}'.format(extension):
            print('Doesn\'t look like you chose a valid file - must end '
                  'with \'.{}\''.format(extension))
            file_ret = str(input(get_file_prompt))
        else:
            break

    return file_ret


def get_int(prompt):
    """This is a data validation function, which provides exception handling
    while collecting an int from user input. Returns that int to the caller."""
    try:
        ret = int(input(prompt))
    except ValueError:
        print('\nMust be a whole number. Try again.')
        ret = get_int(prompt)
    finally:
        return ret

def validate_data(test_df):
    """This function first checks whether the required columns exist. Then,
    It checks whether each item in the Amounts column is a recognizable
    number that can be turned into a float. If either case is not true,
    It will not allow the data to be imported and will send user back to
    menu with an error message. In future, would like to convert these to
    real errors rather than console messages, to support more
    functionality."""
    # other columns to be implemented in future version
    # cols = ['Timestamp', 'Spender', 'Amount', 'Purpose', 'Category']
    cols = ['Spender', 'Amount']
    test_cols = test_df.columns.values.tolist()

    # test that column names are correct.
    for col in cols:
        if col not in test_cols:
            # return False
            print('Column \'' + col + '\' not found. Try another file?')
            return False

    # test that values in 'Amount' are floats
    for index, row in test_df.iterrows():
        try:
            float(row['Amount'])
        except ValueError:
            print ('\nFound incorrectly formatted value in \'Amount\' '
                   f'column, row {index + 1} (after header).\nFix '
                   'values and try the file again, or try another '
                   'file.')
            return False
