# -*- coding: utf-8 -*-
"""
Created on Wed Jan  1 10:35:43 2020

@author: ryder
"""

import os
import pandas as pd
import numpy as np
from pynabapi import YnabClient
import pygsheets
from datetime import datetime as dt
import time
import re



#%% Main Functions

def get_key_from_file(path):
    """
    Reads a key from the first line of a text file stored in the givven path.

    Parameters
    ----------
    path: STRING
        path to the key file.

    Returns
    -------
    _key: STRING
        key string to neccesary API.

    """
    
    with open(path, 'r') as _keyfile:
        _key = _keyfile.readline().strip()

    return(_key)


def load_and_process_sheet(spreadsheet, 
                           lookup_property=None, 
                           lookup_value=None, 
                           start_cell='A1'):
    """
    Loads and processes a spreadsheet from Google Sheets using the pygsheets
    package.

    Parameters
    ----------
    spreadsheet: pygsheets.spreadsheet.Spreadsheet object, required
        Pygsheets spreadsheet object where the worksheet is located. 
        The default is sh.
        
    lookup_property: STRING, required.
        Options: ['title', 'index']. Means with which to look up the desired 
        worksheet from a spreadsheet object. The default is None.
        
    lookup_value: STRING or INT, required
        The default is None enter either a STRING of the title of the worksheet 
        if lookup_property is a string, or an INT of the index of the worksheet 
        if lookup_property is an int.
        
    start_cell: STRING, required
        DESCRIPTION. The default is 'A1'.

    Returns
    -------
    Pandas DataFrame object of selected worksheet.

    """
    
    w = sh.worksheet(lookup_property, lookup_value)
    
    ret_df = w.get_as_df(has_header=True, start=start_cell)

    ret_df.Amount = ret_df.Amount.astype(str).str.extract(r'(\d+)')

    ret_df.Timestamp = pd.to_datetime(ret_df.Timestamp)

    return(ret_df.reset_index(drop=True))



def get_all_transactions_from_google(spreadsheet):
    """
    Convenience function -- calls current month and history tabs and 
    concatenates, then sorts them by Timestamp.
    
    Parameters
    ----------
    spreadsheet: pygsheets.spreadsheet.Spreadsheet object, required
        Pygsheets spreadsheet object where the worksheet is located. 
        The default is sh. 

    Returns
    -------
    Concatenated Pandas DataFrame object of This_Month and History tabs
    together, representing all transactions in Google sheets.

    """

    _this_month = load_and_process_sheet(spreadsheet, 
                                         lookup_property='title', 
                                         lookup_value='This_Month',
                                         start_cell='A2')
    
    _history = load_and_process_sheet(spreadsheet,
                                      lookup_property='title', 
                                      lookup_value='History',
                                      start_cell='A1')
    
    _all_transactions = pd.concat([_this_month, _history])
    
    _all_transactions = _all_transactions.sort_values(by='Timestamp')
    
    return(_all_transactions)




def get_last_google_transaction_date(spreadsheet, 
                                     spender_name='Ryder', 
                                     format='string'):
    """
    Gets the date of the last transaction logged in Google for the provided
    spender.

    Parameters
    ----------
    spreadsheet: pygsheets.spreadsheet.Spreadsheet, required
        Spreadsheet object housing transa. The default is sh.
        
    spender_name: TYPE, optional
        DESCRIPTION. The default is 'Ryder'.
        
    format: string, optional
        options: ['datetime', 'string']. The default is 'string'.

    Returns
    -------
    date of latest transaction by spender in ISO format.

    """
    # Get all transactions in Google Sheets
    _all_trans = get_all_transactions_from_google(spreadsheet)

    _max_date = (_all_trans
                 .loc[_all_trans.Spender == spender_name]['Timestamp'].max())

    if format == 'datetime':
        return(_max_date)
    elif format == 'string':
        return(_max_date.strftime('%Y-%m-%d'))


# Get most recent transaction date for filtering in YNAB



# converting from pynabapi transactions object to dataframe and formatting
def get_shared_transactions_from_ynab(ynab_client, 
                                      ynab_budget_id,
                                      budget_owner,
                                      since_date=None):

    # get budget_id for YNAB from a key file
    with open('keys/ynab_budget_id.txt', 'r') as y_bud_id_txt:
        _YNAB_BUDGET_ID = y_bud_id_txt.readline().strip()   
    
    # get all YNAB transactions in the specified budget. returns transactions obj
    ynab_trans_obj = yc.get_transaction(budget_id=_YNAB_BUDGET_ID)
    
    # convert each trans to a dict, place in list, convert list of dicts to df
    _y_tx_df = pd.DataFrame([vars(t) for t in ynab_trans_obj])
    
    # only keep desired columns for analysis
    keep_cols = ['date', 'amount', 'payee_name', 'memo', 'flag_color']
    _y_tx_df = _y_tx_df[keep_cols]
    
    # only keep shared expenses (flagged as red or purple)
    _y_tx_df = _y_tx_df[_y_tx_df.flag_color.isin(['red', 'purple'])]
    
    # reformat ynab amount field to format as tracked in google
    _y_tx_df.amount = _y_tx_df.amount.divide(-1000).round().astype(int).astype(str)
    
    # convert date field to datetime type
    _y_tx_df.date = pd.to_datetime(_y_tx_df.date)
    
    # rename fields to match google sheet fields
    _y_tx_df = _y_tx_df.rename({'date': 'Timestamp', 
                                'payee_name': 'Vendor', 
                                'amount': 'Amount',
                                'flag_color': 'Purpose',
                                'memo': 'Description'}, axis = 1)
    
    # add appropriate spender
    budget_owner = 'Ryder' # turn into param when wrapping to function
    
    _y_tx_df['Spender'] = budget_owner
    
    
    # tiny function for renaming df.Purpose from red/purple to for us/for you
    def _rename(x):
        if x.Purpose == 'red': return('for us')
        elif x.Purpose == 'purple': return('for you')
        
    # apply function
    _y_tx_df.Purpose = _y_tx_df.apply(_rename, axis=1)
    
    # reset the index from the whole df that removed non red and purple flag items
    _y_tx_df.reset_index(drop=True, inplace=True)
    
    # only get latest transactions if value is passed to since_date
    if since_date is not None:
        
        # internally convert to datetime
        since_date_dt = dt.strptime(since_date, '%Y-%m-%d')
        
        _y_tx_df = (_y_tx_df[_y_tx_df.Timestamp >= since_date_dt]
                    .reset_index(drop=True))
    
    return(_y_tx_df)



def get_last_transaction_date(spender_name, spreadsheet, format='string'):
    """
    Gets the most recent date of the spender specified in the google sheets 
    transaction record.

    Parameters
    ----------
    sh: Google spreadsheet object from pygsheets, required
        A pygsheets spreadsheet object actively connected to. 
        The default is sh.
        
    spender_name: string. required
        The name of the spender whose most recent transaction date in google 
        we are querying.
        
    format: string, required
        Can be either 'datetime' or 'string'. 
        triggers returning the date in either datetime format or as a string. 
        The default is 'datetime'.

    Returns
    -------
    _maxdate (either datetime [default] or string [optional]).

    """

    _gsh_tx_df = get_all_transactions_from_google()

    _maxdate = (
        _gsh_tx_df.loc[_gsh_tx_df.Spender == spender_name]['Timestamp'].max())
    
    if format == 'datetime': 
        return(_maxdate) 
    elif format == 'string':
        return(_maxdate.strftime('%Y-%m-%d'))



def filter_and_prep_new_ynab_transactions(ynab_tx, 
                                          goog_tx, 
                                          since_date):
    
    
    
    _since_date = dt.strptime(since_date, '%Y-%m-%d')

    df_new_ynab_tx = ynab_tx[ynab_tx.Timestamp >= _since_date].reset_index(drop=True)
    
    
    df_new_ynab_tx = pd.merge(df_new_ynab_tx, 
                              goog_tx, 
                              how='left', 
                              indicator=True)
    
    df_new_ynab_tx = df_new_ynab_tx.query(r"_merge == 'left_only'")
    
    df_new_ynab_tx = df_new_ynab_tx.drop('_merge', axis=1)
    
    df_new_ynab_tx.Timestamp = df_new_ynab_tx.Timestamp.astype(str)
    
    df_new_ynab_tx.loc[df_new_ynab_tx.Description.isnull(), 'Description'] = ''
    
    return(df_new_ynab_tx)


def append_new_ynab_transactions_to_google(from_df, 
                                           to_spreadsheet, 
                                           to_worksheet_title):
    
    print('')
    print(from_df)
    print('')
    
        
    this_month = to_spreadsheet.worksheet('title', to_worksheet_title)
    
    while True:
        decision = input('Upload to Expenses Tracker? y/n >> ')
        
        if decision[0].lower() == 'y':
            print('')
            for index, row in from_df.iterrows():
                row_list = [row.Timestamp, row.Spender, row.Amount,
                            row.Vendor, row.Purpose, row.Description]
            
            
                this_month.append_table(row_list)

                print(f'Appending ${float(row.Amount):.0f} - {row.Timestamp} - {row.Vendor} to tracker.')
            
            print(f'\nUploaded ${from_df.Amount.astype(float).sum():.0f} ' \
                  f'over {from_df.shape[0]} transactions.')
            
            break

        elif decision[0].lower() == 'n':
            print('Not entering.')
            break
            
        else:
            print(f'Did not understand entry ({decision}). Try again.')
    
    
