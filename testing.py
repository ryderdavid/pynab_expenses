# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 08:45:36 2019

@author: ryder
"""


import pygsheets as pyg
import sheet_processing_functions as spf
import validation_logic as vl

import pandas as pd


with open('keys/google_expenses_sheet_key.txt', 'r') as g_sheet_id_key_txt:
    GOOGLE_SHEET_ID_KEY = g_sheet_id_key_txt.readline().strip()
#%%
gc = pyg.authorize(service_account_file='keys/service_account_credentials.json')
#%%
sh = gc.open_by_key(GOOGLE_SHEET_ID_KEY)


#%%
# def load_and_process_sheet(sh=sh, tab=0):
#     w = sh.worksheet('index', tab)
#     ret_df = w.get_as_df(has_header=True, start='A2')
#     dollars = ret_df.Amount.astype(str).str.extract(r'(\d+)')
#     # ret_df.loc[:, 'Amount'] = ret_df.Amount.astype(str).str.extract(r'(\d+)')
#     ret_df.Amount = ret_df.Amount.astype(str).str.extract(r'(\d+)')
#     # ret_df.loc[:, 'Timestamp'] = pd.to_datetime(ret_df.Timestamp)
#     ret_df.Timestamp = pd.to_datetime(ret_df.Timestamp)

#     return(ret_df.reset_index(drop=True))
#     # return(dollars)


#%%

colnames = ['Timestamp', 'Payee', 'Amount', 'Purpose', 'Description']
all_sheets = pd.DataFrame(columns = colnames)

#%%
for sheetnum in range(len(sh.worksheets())):
    curr_sheet = spf.load_and_process_sheet(sh, sheetnum)

    # if curr_sheet.shape[1] != 5:
    #     skip

    # print(curr_sheet.columns)
    all_sheets = all_sheets.append(curr_sheet)


#%%

w = sh.worksheet('index', value = 1)
#%%
ret_df = w.get_as_df(has_header=True, start='A2')
#%%
ret_df.loc[:, 'Amount'] = ret_df.Amount.astype(str).str.extract(r'(\d+)')