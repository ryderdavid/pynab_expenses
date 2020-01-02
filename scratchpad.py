# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 12:23:01 2019

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

os.chdir(r'C:\Users\ryder\Projects\pynab_expenses')

import sheet_processing_functions as spf



#%% #%%
# should create google_ledger object
with open('keys/google_expenses_sheet_key_dev.txt', 'r') as g_sheet_id_key_txt:
    GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()

gc = pygsheets.authorize(service_account_file='keys/service_account_credentials.json')

sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)


#%%
# get History worksheet as dataframe
history = sh.worksheet(property='title', value='History').get_as_df()

#%%
history.reset_index(level=0, inplace=True)

#%%
history.to_csv('transaction_history.csv', index=False)