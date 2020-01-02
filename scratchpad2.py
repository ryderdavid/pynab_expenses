# -*- coding: utf-8 -*-
"""
Created on Wed Jan  1 10:35:43 2020

@author: ryder
"""

import os
import pandas as pd
from pynabapi import YnabClient
import pygsheets
import datetime
import time
import re

os.chdir(r'C:\Users\ryder\Projects\pynab_expenses')



with open('keys/google_expenses_sheet_key_dev.txt', 'r') as g_sheet_id_key_txt:
    GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()

gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')

sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)

# import sheet_processing_functions as spf

#%% Get all transactions in google, current month and historical

def load_and_process_sheet(sh=sh, 
                           lookup_property=None, 
                           lookup_value=None, 
                           start_cell='A2'):
    
    w = sh.worksheet(lookup_property, lookup_value)
    
    ret_df = w.get_as_df(has_header=True, start=start_cell)

    ret_df.Amount = ret_df.Amount.astype(str).str.extract(r'(\d+)')

    ret_df.Timestamp = pd.to_datetime(ret_df.Timestamp)

    return(ret_df.reset_index(drop=True))


#%% 

def get_all_transactions_from_google():

    _this_month = load_and_process_sheet(lookup_property='title', 
                                          lookup_value='This_Month',
                                          start_cell='A2')
    
    _history = load_and_process_sheet(lookup_property='title', 
                                          lookup_value='History',
                                          start_cell='A1')
    
    _all_transactions = pd.concat([_this_month, _history])
    
    _all_transactions = _all_transactions.sort_values(by='Timestamp')
    
    return(_all_transactions)



#%%

all_transactions_from_google = get_all_transactions_from_google()




#%% Get most recent transaction date for filtering in YNAB

def get_last_transaction_date(sh=sh, payee='Ryder', format='datetime'):

    # Get all transactions in Google Sheets
    _all_trans = get_all_transactions_from_google()

    _max_date = _all_trans.loc[_all_trans.Payee == payee]['Timestamp'].max()

    if format == 'datetime':
        return(_max_date)
    elif format == 'string':
        return(_max_date.strftime('%Y-%m-%d'))
    
#%%
maxdate= get_last_transaction_date()



#%%

# get YNAB client key from key file
with open('keys/ynab_api_key.txt', 'r') as y_api_key_txt:
    YNAB_CLIENT_KEY = y_api_key_txt.readline().strip()
    
# get budget_id for YNAB from a key file
with open('keys/ynab_budget_id.txt', 'r') as y_bud_id_txt:
    YNAB_BUDGET_ID = y_bud_id_txt.readline().strip()   

# establish a client connection with YNAB API
yc = YnabClient(YNAB_CLIENT_KEY)

# get all YNAB transactions in the specified budget. returns transactions obj
ynab_trans_obj = yc.get_transaction(budget_id=YNAB_BUDGET_ID)



 
#%% convert each trans to a dict, place in list, convert list of dicts to df
ynab_trans_df = pd.DataFrame([vars(t) for t in ynab_trans_obj])

# only keep desired columns for analysis
keep_cols = ['date', 'payee_name', 'memo', 'flag_color', 'amount']

ynab_trans_df = ynab_trans_df[keep_cols]

# only keep shared expenses (flagged as red or purple)
ynab_trans_df = ynab_trans_df[ynab_trans_df.flag_color.isin(['red', 'purple'])]

#%%




#%%

def get_trans_from_ynab(sh=sh, since_date=get_last_transaction_date()):

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

    ret_df = pd.DataFrame(
        columns = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description'])


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
