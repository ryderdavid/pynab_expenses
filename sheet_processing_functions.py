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
import datetime
import time
import re

#%%


# should create google_ledger object
with open('keys/google_expenses_sheet_key_dev.txt', 'r') as g_sheet_id_key_txt:
    GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()

gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')

sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)


#%% GOOGLE FUNCTIONS

def load_and_process_sheet(sh=sh, tab=0, start_cell='A2'):

    w = sh.worksheet('index', tab)
    ret_df = w.get_as_df(has_header=True, start=start_cell)

    ret_df.Amount = ret_df.Amount.astype(str).str.extract(r'(\d+)')

    ret_df.Timestamp = pd.to_datetime(ret_df.Timestamp)

    return(ret_df.reset_index(drop=True))


# def get_all_googlesheet_transactions(sh=sh):
    
#     colnames = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description']
    
#     all_sheets = pd.DataFrame(columns = colnames)
    
    



def load_and_process_all_sheets(sh=sh):

    colnames = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description']
    all_sheets = pd.DataFrame(columns = colnames)

    for sheetnum in range(len(sh.worksheets())):

        curr_sheet = load_and_process_sheet(sh, sheetnum)
    
        sheet_title = re.search(r'(?<=Worksheet ).+(?= index)',
                                str(sh.worksheets()[1])).group(0)
    
        if curr_sheet.shape[1] != 5:
    
            raise Exception(f'Worksheet {sheet_title} (index {sheetnum} has the '
                            f'wrong dimensions.')
    
        # print(curr_sheet.columns)
        all_sheets = all_sheets.append(curr_sheet)

    return(all_sheets.sort_values('Timestamp', ascending=False))

#%%
def get_last_trns_date(sh=sh, payee_name = 'Ryder', format = 'datetime'):

    # Get all transactions in Google Sheets
    __all_trans = load_and_process_all_sheets()

    __max_date = (
            __all_trans
            .loc[__all_trans.Payee == payee_name]['Timestamp']
            .max()
            )

    if format == 'datetime':
        return(__max_date)
    elif format == 'string':
        return(__max_date.strftime('%Y-%m-%d'))


#%%
def get_trans_from_ynab(sh=sh, since_date=get_last_trns_date()):

    # since_date = get_last_trns_date()

    with open('keys/ynab_api_key.txt', 'r') as y_api_key_txt:
        YNAB_CLIENT_KEY = y_api_key_txt.readline().strip()

    with open('keys/ynab_budget_id.txt', 'r') as y_bud_id_txt:
        YNAB_BUDGET_ID = y_bud_id_txt.readline().strip()

    yc = YnabClient(YNAB_CLIENT_KEY)

    all_transactions = yc.get_transaction(budget_id=YNAB_BUDGET_ID)

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

    ynab_df_filter = (
            ynab_df[(ynab_df.timestamp >= since_date) &
                    (ynab_df.flag.isin(['red', 'purple']))]
        )

    ret_df = pd.DataFrame(columns = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description'])


    ret_df.Timestamp = ynab_df_filter.timestamp.astype(str) + ' 00:00:00'
    ret_df.Payee = 'Ryder'
    ret_df.Amount = ynab_df_filter.amount.round(0).astype(int).astype(str)
    
    # apply for us for red flags, and for you for purple flags
    ret_df.Purpose = (ynab_df_filter.flag.apply(lambda x:
        'for us' if x == 'red' else 'for you' if x == 'purple' else '-1'))
    
    ret_df.Description = (
            (ynab_df_filter.payee + ' - ' + ynab_df_filter.memo)
            .str.replace(' - None', '')
            )

    return(ret_df)


#%%
def get_expenses_from_google(sh=sh, since_date='1900-01-01'):

    colnames = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description']
    all_sheets = pd.DataFrame(columns = colnames)

    for sheetnum in range(len(sh.worksheets())):

        curr_sheet = load_and_process_sheet(sh, sheetnum)
    
        sheet_title = re.search(r'(?<=Worksheet ).+(?= index)',
                                str(sh.worksheets()[1])).group(0)
    
        if curr_sheet.shape[1] != 5:
    
            raise Exception(f'Worksheet {sheet_title} (index {sheetnum} has the '
                            f'wrong dimensions.')
    
        # print(curr_sheet.columns)
        all_sheets = all_sheets.append(curr_sheet)



    since_date_datetime = datetime.datetime.strptime(since_date, '%Y-%m-%d')

    ret_expenses_from_google = (
            all_sheets
                .loc[all_sheets.Timestamp >= since_date_datetime]
                .sort_values('Timestamp', ascending = False)

            )

    ret_expenses_from_google.Timestamp = (
            ret_expenses_from_google.Timestamp.astype(str)
            )

    return(ret_expenses_from_google)


#%%
def get_new_ynab_expenses_to_upload():

    # Get most recent date from Google expenses
    since_date=get_last_trns_date(format='string')
    
    # Get most recent Google shared expenses
    recent_from_gs = get_expenses_from_google(since_date=since_date)
    
    # Get my recent YNAB expenses
    recent_from_ynab = get_trans_from_ynab(since_date=since_date)
    
    # Set operation: return only those YNAB expenses NOT also in Google sheets
    in_ynab_not_google = (
            recent_from_ynab.merge(recent_from_gs, how = 'left', indicator = True)
            .query('_merge == \'left_only\'')
            .drop('_merge', 1)
            )

    return(in_ynab_not_google)




#%%
def append_to_expenses_sheet(expenses_to_upload):

    print('')
    print(expenses_to_upload)
    print('')

    this_month = sh.worksheet('index', 0)


    while True:
        decision = input('Upload to Expenses Tracker? y/n >> ')
        
        if decision[0].lower() == 'y':
            print('')
            for index, row in expenses_to_upload.iterrows():
                row_list = [row.Timestamp, row.Payee, row.Amount,
                            row.Purpose, row.Description]
            
            
                this_month.append_table(row_list)

                print(f'Appending ${float(row.Amount):.0f} - {row.Description} to tracker.')
            
            print(f'\nUploaded ${expenses_to_upload.Amount.astype(float).sum():.0f} ' \
                  f'over {expenses_to_upload.shape[0]} transactions.')
            
            break

        elif decision[0].lower() == 'n':
            print('Not entering.')
            break
            
        else:
            print(f'Did not understand entry ({decision}). Try again.')





          



def archive_sheet_and_clear(sheet=sh):

    w = load_and_process_sheet(sh, tab=0)

    date_max = w.Timestamp.max().strftime('%m/%d/%Y')
    date_min = w.Timestamp.min().strftime('%m/%d')
    
    tab_title = date_min + '-' + date_max
    
    wks = sh.worksheet('index', 0)
    sh.add_worksheet(tab_title, src_worksheet=wks)
    wks.clear(start='A3')


def show_spender_information(sheet=sh):
    w_df = load_and_process_sheet(sheet, tab=0)
    spender_list = w_df.Payee.unique()

    amounts_list = []

    for i, name in enumerate(spender_list):
        total_shared_transactions_amt = w_df[w_df.Purpose == 'for us'].sum()
        spenders_shared_transactions_amt = (
                w_df[(w_df.Payee == name) & w_df.Purpose == 'for us']
                )

        print(total_shared_transactions_amt)
