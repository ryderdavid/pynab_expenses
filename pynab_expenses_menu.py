# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 10:33:55 2019

@author: ryder
"""

# import os
import pygsheets
import sheet_processing_functions
import validation_logic






if __name__ == "__main__":

    # gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')

    # sh = gc.open_by_key(GOOGLE_SHEET_KEY)

    def menu():
        while True:
            print('\n1: Import latest YNAB expenses')
            print('2: Show spender information')
            print('3: Archive current month sheet')
            print('4: Exit')
            menu_choice = validation_logic.get_int('Enter a choice: ')

            if menu_choice == 1:
                # Get YNAB expenses
                sheet_processing_functions.import_transactions_from_ynab()
                continue
            elif menu_choice == 2:
                pass
            elif menu_choice == 3:
                sheet_processing_functions.archive_sheet_and_clear()
                print('\nArchived this month\'s data.')
            elif menu_choice == 4:
                break

            else:
                print('Please choose an option from 1 to 4.')


    menu()
    print('\nProgram exiting. Goodbye.')
