# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 10:33:55 2019

@author: ryder
"""

# import os
import pygsheets
import sheet_processing_functions_2 as spf
import validation_logic

#%%





if __name__ == "__main__":

    os.chdir(r'C:\Users\ryder\Projects\pynab_expenses')

    YNAB_API_KEY = get_key_from_file(r'keys\ynab_api_key.txt')
    
    YNAB_BUDGET_ID = get_key_from_file(r'keys\ynab_budget_id.txt')
    
    GOOGLE_SHEET_KEY = get_key_from_file(r'keys\google_expenses_sheet_key_dev.txt')
    
    
    # connect to YNAB and to Google Sheet
    yc = YnabClient(YNAB_API_KEY)
    gc = pygsheets.authorize(service_account_file=r'keys\service_acct_creds.json')
    sh = gc.open_by_key(GOOGLE_SHEET_KEY)

    def menu():
        while True:
            print('\n1: Get latest YNAB expenses')
            print('2: Show spender information')
            print('3: Archive current month sheet')
            print('4: Exit')
            menu_choice = validation_logic.get_int('Enter a choice: ')

            if menu_choice == 1:
                
                df_all_goog_tx = get_all_transactions_from_google(sh)
                
                last_tx_date = (
                    get_last_google_transaction_date(sh, budget_owner='Ryder'))
                
                df_all_ynab_tx = 
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
