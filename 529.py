#!/usr/local/bin/python -u

'''
    This script calculates the average difference between two 
    scenarios.
    
    The original one-off script examined two refinance situations but I quickly
    repurposed this script to examine your 529 plan question.
    
    The 'beauty' of the program is it simulates the year-to-year variability in
    stock market performance by sampling from historical stock market
    performances, over many thousands of simulations. This approach captures
    the stochasticity in markets better than parametric summary statistics such
    as variance or standard deviation could.
    
    All parameters are set by changing global variables.

    We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/
    
'''

import os.path
import random
import csv

path = os.path.dirname(__file__)
HISTORICAL_DATA         = os.path.join(path, 'historical_market_index_data.csv')
OUTFILE_NAME            = os.path.join(path, 'histogram.pdf') 

# tax bracket LUTs
MD_STATE_TAX_2014 = {'Single':  { '$0+'       : .0200,
                                  '$1,000'    : .0300,
                                  '$2,000'    : .0400,
                                  '$3,000'    : .0475,
                                  '$100,000+' : .0500,
                                  '$125,000+' : .0525,
                                  '$150,000+' : .0550,
                                  '$200,000+' : .0575},
                     'Couple':  { '$0+'       : .0200,
                                  '$1,000'    : .0300,
                                  '$2,000'    : .0400,
                                  '$3,000'    : .0475,
                                  '$150,000+' : .0500,
                                  '$175,000+' : .0525,
                                  '$225,000+' : .0550,
                                  '$300,000+' : .0575}
                    }

MD_COUNTY_TAX_2014 = {  'Allegany County'       : .0305,
                        'Anne Arundel County'   : .0256,
                        'Baltimore'             : .0305,
                        'Baltimore County'      : .0283,
                        'Calvert County'        : .0280,
                        'Caroline County'       : .0263,
                        'Carroll County'        : .0305,
                        'Cecil County'          : .0280,
                        'Charles County'        : .0290,
                        'Dorchester County'     : .0262,
                        'Frederick County'      : .0296,
                        'Garrett County'        : .0265,
                        'Harford County'        : .0306,
                        'Howard County'         : .0320,
                        'Kent County'           : .0285,
                        'Montgomery County'     : .0320,
                        'Prince Georges County' : .0320,
                        'Queen Annes County'    : .0285,
                        'Somerset County'       : .0315,
                        'St. Marys County'      : .0300,
                        'Talbot County'         : .0225,
                        'Washington County'     : .0280,
                        'Wicomico County'       : .0310,
                        'Worcester County'      : .0125}


# choose the index you want to use for the simulation.
# Options are: 'DJIA', 'Wilshire_5000', 'S&P500',
#              '3_Month_Treasury', '10_Year_Treasury'
INDEX                   = 'Wilshire_5000'
SIMULATIONS             = 100000
STARTING_INVESTMENT     = 0.
NUM_OF_YEARS            = 18
ANNUAL_INVESTMENT       = 2500.
PLAN_1_EXPENSE_RATIO    = 0.0088
PLAN_1_TAX_BENEFIT      = MD_STATE_TAX_2014['Couple']['$150,000+'] + \
                          MD_COUNTY_TAX_2014['Montgomery County']
PLAN_2_EXPENSE_RATIO    = 0.0019
PLAN_2_TAX_BENEFIT      = 0.



# import historical market index data from csv file
with open(HISTORICAL_DATA, 'rb') as csvfile:
    rows = csv.DictReader(csvfile)
    historical_performances = [row[INDEX] for row in rows if row[INDEX] <> '']

print '                   Starting Investment: ${STARTING_INVESTMENT:,.0f}\n'\
      '           Annual Investment into Plan: ${ANNUAL_INVESTMENT:,.0f}\n'\
      '                       Number of Years: {NUM_OF_YEARS} years\n'\
      '                  Plan 1 Expense Ratio: {PLAN_1_EXPENSE_RATIO:.2%}\n'\
      '                    Plan 1 Tax Benefit: {PLAN_1_TAX_BENEFIT:.2%}\n'\
      '                  Plan 2 Expense Ratio: {PLAN_2_EXPENSE_RATIO:.2%}\n'\
      '                    Plan 2 Tax Benefit: {PLAN_2_TAX_BENEFIT:.2%}\n'\
      '                 Historical Index Used: {INDEX}\n\n'\
      '                         Calculating... {SIMULATIONS:,} simulations'\
      ''.format(**locals())

plan_1_results = []
plan_2_results = []
differences = []
for i in range(SIMULATIONS):
    investment1 = investment2 = STARTING_INVESTMENT
    carryover_deductible1 = carryover_deductible2 = STARTING_INVESTMENT
    for year in range(NUM_OF_YEARS):
        performance = random.choice(historical_performances)
        investment1 += ANNUAL_INVESTMENT
        investment1 *= 1 + float(performance)-PLAN_1_EXPENSE_RATIO
        
        investment2 += ANNUAL_INVESTMENT
        investment2 *= 1 + float(performance)-PLAN_2_EXPENSE_RATIO
        
        # now calculate and reinvest the tax benefit
        # (really?? that's not going to happen, at least not automatically)
        carryover_deductible1 += ANNUAL_INVESTMENT
        deductible1 = 2500. if carryover_deductible1 > 2500. else carryover_deductible1
        carryover_deductible1 -= deductible1
        investment1 += deductible1*PLAN_1_TAX_BENEFIT
        
        carryover_deductible2 += ANNUAL_INVESTMENT
        deductible2 = 2500. if carryover_deductible2 > 2500. else carryover_deductible2
        carryover_deductible2 -= deductible2 
        investment2 += deductible2*PLAN_2_TAX_BENEFIT
              
    plan_1_results.append(investment1)
    plan_2_results.append(investment2)
    differences.append(investment2-investment1)
plan_1_results.sort()
plan_2_results.sort()
differences.sort()


# find the first positive number in the sorted results list.
for i, result in enumerate(differences):
    if result > 0:
        likelihood = 1-i/float(len(differences))
        break
else:
    likelihood = 0.

print '            Plan 1 Median Final Amount: ${p1_median:,.0f} '\
      '(95% HPD: ${p1_hpd_low:,.0f} to ${p1_hpd_high:,.0f})\n'\
      '            Plan 2 Median Final Amount: ${p2_median:,.0f} '\
      '(95% HPD: ${p2_hpd_low:,.0f} to ${p2_hpd_high:,.0f})\n'\
      '                     Median Difference: ${diff_median:,.0f} '\
      '(95% HPD: ${diff_hpd_low:,.0f} to ${diff_hpd_high:,.0f})\n'\
      '   Likelihood that Plan 2 beats Plan 1: {likelihood:.2%}'\
      ''.format(p1_median = plan_1_results[int(0.5*SIMULATIONS)],
                p1_hpd_low = plan_1_results[int(0.025*SIMULATIONS)],
                p1_hpd_high = plan_1_results[int(0.975*SIMULATIONS)],
                p2_median = plan_2_results[int(0.5*SIMULATIONS)],
                p2_hpd_low = plan_2_results[int(0.025*SIMULATIONS)],
                p2_hpd_high = plan_2_results[int(0.975*SIMULATIONS)],
                diff_median = differences[int(0.5*SIMULATIONS)],
                diff_hpd_low = differences[int(0.025*SIMULATIONS)],
                diff_hpd_high = differences[int(0.975*SIMULATIONS)],
                likelihood = likelihood)
