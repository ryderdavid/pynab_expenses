# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 10:33:55 2019

@author: ryder
"""

# import os
import pygsheets
import sheet_processing_functions as spf
import validation_logic

#%%





if __name__ == "__main__":

    # with open('keys/google_expenses_sheet_key_dev.txt', 'r') as g_sheet_id_key_txt:
    #     GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()
    
    # gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')
    
    # sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)

    def menu():
        while True:
            print('\n1: Get latest YNAB expenses')
            print('2: Show spender information')
            print('3: Archive current month sheet')
            print('4: Exit')
            menu_choice = validation_logic.get_int('Enter a choice: ')

            if menu_choice == 1:
                new_expenses = spf.get_new_ynab_expenses_to_upload()
                spf.append_to_expenses_sheet(new_expenses)

                continue
            elif menu_choice == 2:
                pass
            elif menu_choice == 3:
                spf.archive_sheet_and_clear()
                print('\nArchived this month\'s data.')
            elif menu_choice == 4:
                break

            else:
                print('Please choose an option from 1 to 4.')


    menu()
    print('\nProgram exiting. Goodbye.')
