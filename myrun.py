#!/usr/local/bin/python -u

'''
    This run file calculates the final principals of various 529 plan 
    investment scenarios.
    
    This script just sets parameters and calls the model. 
    
    We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/
'''

import model

s1 = model.Scenario(
        name                   = 'Maryland College Investment Plan',
        starting_investment    = 0.,
        annual_investment      = 2500.,
        num_of_years           = 18,
        expense_ratio          = model.MD_EXPENSE_RATIO,
        tax_benefit_ratio      = model.MD_STATE_TAX_2014['Couple']['$3,000'] \
                                 + model.MD_COUNTY_TAX_2014['Montgomery County'],
        index                  = 'Wilshire_5000')
s2 = model.Scenario(
        name                   = 'Nevada Vanguard Plan',
        starting_investment    = 0.,
        annual_investment      = 2500.,
        num_of_years           = 18,
        expense_ratio          = model.VANGUARD_EXPENSE_RATIO,
        tax_benefit_ratio      = 0.,
        index                  = 'Wilshire_5000')
s3 = model.Scenario(
        name                   = 'MD with Y10 rollover',
        starting_investment    = 0.,
        annual_investment      = 2500.,
        num_of_years           = 18,
        expense_ratio          = model.MD_EXPENSE_RATIO,
        tax_benefit_ratio      = model.MD_STATE_TAX_2014['Couple']['$3,000'] \
                                 + model.MD_COUNTY_TAX_2014['Montgomery County'],
        rollover_tax_benefit_ratio = 0.,
        rollover_expense_ratio = model.VANGUARD_EXPENSE_RATIO,
        rollover_year          = 9,
        index                  = 'Wilshire_5000')

for scenario in [s1, s2, s3]:
    scenario.simulate()