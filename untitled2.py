# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 17:52:29 2020

@author: ryder
"""

spf.get_new_ynab_expenses_to_upload(
                    ynab_client=yc,
                    ynab_budget_id=YNAB_BUDGET_ID,
                    budget_owner='Ryder',
                    since_date=get_last_google_transaction_date(sh,
                                                                budget_owner)
                    )