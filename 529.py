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

MD_EXPENSE_RATIO        = 0.0088
VANGUARD_EXPENSE_RATIO  = 0.0019

class Scenario:
    def __init__(self, name = None, starting_investment = None, annual_investment = None,
                 expense_ratio = None, tax_benefit = None):
        self.name = name
        self.starting_investment = starting_investment
        self.annual_investment = annual_investment
        self.expense_ratio = expense_ratio
        self.tax_benefit = tax_benefit
        self.investment = None
        self.carryover_deductible = None
        self.results = []

###############

# Define models here.

SIMULATIONS             = 100000
NUM_OF_YEARS            = 18

# for historical_index, choose the index you want to use for the simulation.
# Options are: 'DJIA', 'Wilshire_5000', 'S&P500',
#              '3_Month_Treasury', '10_Year_Treasury'
INDEX                   = 'Wilshire_5000'

SCENARIOS = [Scenario(name                  = 'Maryland College Investment Plan',
                      starting_investment   = 0.,
                      annual_investment     = 2500.,
                      expense_ratio         = MD_EXPENSE_RATIO,
                      tax_benefit           = MD_STATE_TAX_2014['Couple']['$150,000+'] \
                                              + MD_COUNTY_TAX_2014['Montgomery County']),
             Scenario(name                  = 'Nevada Vanguard Plan',
                      starting_investment   = 0.,
                      annual_investment     = 2500.,
                      expense_ratio         = VANGUARD_EXPENSE_RATIO,
                      tax_benefit           = 0.)]

# import historical market index data from csv file
with open(HISTORICAL_DATA, 'rb') as csvfile:
    rows = csv.DictReader(csvfile)
    historical_performances = [float(row[INDEX]) for row in rows if row[INDEX] <> '']
    
print '                       Number of Years: {NUM_OF_YEARS} years\n'\
      '                 Historical Index Used: {INDEX}\n'\
      '                         Calculating... {SIMULATIONS:,} simulations\n'\
      ''.format(**locals())

for i in range(SIMULATIONS):
    for scenario in SCENARIOS:
        scenario.investment = scenario.starting_investment
        scenario.carryover_deductible = scenario.starting_investment
    for year in range(NUM_OF_YEARS):
        performance = random.choice(historical_performances)
        for scenario in SCENARIOS:
            scenario.investment += scenario.annual_investment
            scenario.investment *= 1 + performance-scenario.expense_ratio
            # now calculate and reinvest the tax benefit (reinvestment is unrealistic)
            scenario.carryover_deductible += scenario.annual_investment
            if scenario.carryover_deductible > 2500:
                deductible = 2500.
            else:
                deductible = scenario.carryover_deductible
            scenario.carryover_deductible -= deductible
            scenario.investment += deductible*scenario.tax_benefit
    for scenario in SCENARIOS:
        scenario.results.append(scenario.investment)
for i, scenario in enumerate(SCENARIOS):
    scenario.results.sort()
    median = scenario.results[int(0.5*SIMULATIONS)]
    hpd_low = scenario.results[int(0.025*SIMULATIONS)]
    hpd_high = scenario.results[int(0.975*SIMULATIONS)]
    print '                            Scenario {i}: {scenario.name}\n' \
          '                         Expense Ratio: {scenario.expense_ratio:.2%}\n'\
          '                     State Tax Benefit: {scenario.tax_benefit:.2%}\n'\
          '                   Starting Investment: ${scenario.starting_investment:,.0f}\n'\
          '           Annual Investment into Plan: ${scenario.annual_investment:,.0f}\n'\
          '                   Median Final Amount: ${median:,.0f} '\
          '(95% HPD: ${hpd_low:,.0f} to ${hpd_high:,.0f})\n'\
          ''.format(**locals())