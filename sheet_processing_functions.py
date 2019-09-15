# -*- coding: utf-8 -*-
"""
Created on Sat Sep  7 18:40:45 2019

@author: ryder
"""

#%%
import os
import pandas as pd
from pynabapi import YnabClient
import pygsheets
import time

#%%

with open('keys/google_expenses_sheet_key.txt', 'r') as g_sheet_id_key_txt:
    GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()

gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')

sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)


def load_and_process_sheet(sh=sh, tab=0):
    w = sh.worksheet('index', tab)
    ret_df = w.get_as_df(has_header=True, start='A2')
    ret_df.loc[:, 'Amount'] = ret_df.Amount.astype(str).str.extract(r'(\d+)')
    ret_df.loc[:, 'Timestamp'] = pd.to_datetime(ret_df.Timestamp)

    return(ret_df.reset_index(drop=True))


def import_transactions_from_ynab(sh=sh):

    def get_last_trns_date(sh=sh):
    
        max_date = pd.to_datetime('1900-12-31')
    
        for sheet_num in range(len(sh.worksheets())):
            worksheet = load_and_process_sheet(sh, sheet_num)
            ry_ws_transactions = worksheet[worksheet.Payee == 'Ryder']
        
            # if no Ryder transactions then go to next sheet
            if ry_ws_transactions.shape[0] == 0:
                continue
        
            else:
                worksheet_max_date = ry_ws_transactions.Timestamp.max()
                max_date = worksheet_max_date if worksheet_max_date > max_date else max_date


        return(max_date.strftime('%Y-%m-%d'))


    since_date = get_last_trns_date(sh)
    
    
    """
    YNAB API SECTION
    -------------------
    To document
    """

    with open('keys/ynab_api_key.txt', 'r') as y_api_key_txt:
        YNAB_CLIENT_KEY = y_api_key_txt.readline().strip()

    with open('keys/ynab_budget_id.txt', 'r') as y_bud_id_txt:
        YNAB_BUDGET_ID = y_bud_id_txt.readline().strip()



    ynab_client = YnabClient(
        YNAB_CLIENT_KEY)



    # my_budgets = ynab_client.get_budget()
    
    all_transactions = ynab_client.get_transaction(
        budget_id=YNAB_BUDGET_ID)


    column_names = ['timestamp', 'payee', 'memo', 'flag', 'amount']
    listofitems = []
    
    for item in all_transactions:
        listofitems.append(str(item.date)        + ',,,' + 
                           str(item.payee_name)  + ',,,' +
                           str(item.memo)        + ',,,' +
                           str(item.flag_color)  + ',,,' +
                           str(item.amount)
                          )
    
    
    ynab_df = pd.Series(listofitems).str.split(',,,', expand=True)
    ynab_df.columns = column_names
    ynab_df.timestamp = pd.to_datetime(ynab_df.timestamp)
    ynab_df.amount = ynab_df.amount.astype(int) / -1000
    
    
    # get just items past a certain date and that are shared or 'for you' expenses
    ynab_df_filter = (
            ynab_df[(ynab_df.timestamp >= since_date) &
                    (ynab_df.flag.isin(['red', 'purple']))]
        )
    
    # print(f'\nMost recent day with Ryder\'s transactions is {since_date}. ' \
    #       f'Getting shared items since then.')
    # time.sleep(1)
    # print(f'\nFound {ynab_df_filter.shape[0]} transactions. Uploading them!\n')
    
    
    """
    GOOGLE SHEET UPLOAD
    """
    
    ryder_expenses_upload = pd.DataFrame(columns = ['Timestamp', 'Payee',
                                                    'Amount', 'Purpose',
                                                    'Description'])
    
    ryder_expenses_upload.Timestamp = ynab_df_filter.timestamp.astype(str) + ' 00:00:00'
    ryder_expenses_upload.Payee = 'Ryder'
    ryder_expenses_upload.Amount = ynab_df_filter.amount.round(0)
    
    # apply for us for red flags, and for you for purple flags
    ryder_expenses_upload.Purpose = (ynab_df_filter.flag.apply(lambda x:
        'for us' if x == 'red' else 'for you' if x == 'purple' else '-1'))
    
    ryder_expenses_upload.Description = (
            (ynab_df_filter.payee + ' - ' + ynab_df_filter.memo)
            .str.replace(' - None', '')
            )
    
    
    #%% Append to Expenses! Spreadsheet
    wks = sh.worksheet('index', 0)

    wks_df = wks.get_as_df(has_header=True, start='A2')
    wks_df = wks_df[(wks_df.Payee == 'Ryder') & (wks_df.Timestamp >= since_date)]

    ryder_expenses_upload = pd.concat([ryder_expenses_upload, wks_df]).drop_duplicates(keep=False).reset_index(drop=True)

    print('')
    for index, row in ryder_expenses_upload.iterrows():
        row_list = [row.Timestamp, row.Payee, row.Amount,
                    row.Purpose, row.Description]
    
    
        wks.append_table(row_list)

        print(f'Appending ${row.Amount:.0f} - {row.Description} to tracker.')
    
    print(f'\nUploaded ${ryder_expenses_upload.Amount.sum():.0f} ' \
          f'over {ryder_expenses_upload.shape[0]} transactions.')
    
    # print('')
    # x = input("Press ENTER to exit.")

def archive_sheet_and_clear(sheet=sh):

    w = load_and_process_sheet(sh, tab=0)

    date_max = w.Timestamp.max().strftime('%m/%d/%Y')
    date_min = w.Timestamp.min().strftime('%m/%d')
    
    tab_title = date_min + '-' + date_max
    
    wks = sh.worksheet('index', 0)
    sh.add_worksheet(tab_title, src_worksheet=wks)
    wks.clear(start='A3')