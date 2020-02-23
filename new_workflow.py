# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 10:50:42 2020

@author: ryder
"""

import os
import pandas as pd
import numpy as np
from pynabapi import YnabClient
import pygsheets
import datetime
import time
import re

os.chdir(r'C:\Users\ryder\Projects\pynab_expenses')


#%% Define important keystrings
YNAB_API_KEY = get_key_from_file(r'keys\ynab_api_key.txt')

YNAB_BUDGET_ID = get_key_from_file(r'keys\ynab_budget_id.txt')

GOOGLE_SHEET_KEY = get_key_from_file(r'keys\google_expenses_sheet_key_dev.txt')


# connect to YNAB and to Google Sheet
yc = YnabClient(YNAB_API_KEY)
gc = pygsheets.authorize(service_account_file=r'keys\service_acct_creds.json')
sh = gc.open_by_key(GOOGLE_SHEET_KEY)

#%% get all google sheets transactions first
df_all_goog_tx = get_all_transactions_from_google(spreadsheet=sh)

#%% get most recent transaction by spender
latest_tx_date = get_last_google_transaction_date(spreadsheet=sh,
                                                  spender_name='Ryder',
                                                  format='string')

#%% get ynab transactions since that date

df_all_ynab_tx = get_shared_transactions_from_ynab(yc,
                                                   YNAB_BUDGET_ID,
                                                   budget_owner='Ryder')


#%%
df_new_ynab_tx = filter_and_prep_new_ynab_transactions(ynab_tx=df_all_ynab_tx,
                                                       goog_tx=df_all_goog_tx,
                                                       since_date=latest_tx_date)



#%%
df_new_ynab_tx


#%%
append_new_ynab_transactions_to_google(from_df=df_new_ynab_tx,
                                       to_spreadsheet=sh,
                                       to_worksheet_title='This_Month')

