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
import numpy
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

# 0.50% is the 2015 expense ratio of the global equity market index portfolio,
# which is the only passive stock index investment fund in the MD plan. :-/ This
# portfolio is not bad, except that it is missing emerging markets and global
# small caps. It is similar to TSP split  C - 56%; S - 14%; I - 30%.
# If we pick the target funds (which are actively managed and thus liable to do worse
# than the Wilshire 5000), the 2015 expense ratio is 0.80%.
# There are no passive bond investment funds in the MD plan. The closest is Inflation
# Focused Bond Fund, which has a 2015 expense ratio of 0.68%. The
# MD Bond/Income Fund contains a large number of junk bonds and its returns
# are going to be highly correlated with equity returns; hence, it doesn't add anything
# to a properly balanced and diversified portfolio.
# An accurate simulation should support equity/bond splits with rebalancing and also
# glide paths. 100% equities (stocks) until college age is very risky (just look at
# the 95% HPDs) and not representative of most 529 plan investments.
MD_EXPENSE_RATIO        = 0.0050
VANGUARD_EXPENSE_RATIO  = 0.0019

class Scenario:
    '''
        Convenient container for all of the variables needed to define each
        scenario.
    '''
    def __init__(self, name = None, starting_investment = None, annual_investment = None,
                 expense_ratio = None, tax_benefit = None, rollover_expense_ratio = None,
                 rollover_year = None, rollover_tax_benefit = 0.):
        self.name = name
        self.starting_investment = starting_investment
        self.annual_investment = annual_investment
        self.expense_ratio = expense_ratio
        self.tax_benefit = tax_benefit
        self.rollover_expense_ratio = rollover_expense_ratio
        self.rollover_year = rollover_year
        self.rollover_tax_benefit = rollover_tax_benefit
        # the remaining vars should not have initial values and are used as 
        # part of the calculation algorithm
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
                      tax_benefit           = MD_STATE_TAX_2014['Couple']['$3,000'] \
                                              + MD_COUNTY_TAX_2014['Montgomery County']),
             Scenario(name                  = 'Nevada Vanguard Plan',
                      starting_investment   = 0.,
                      annual_investment     = 2500.,
                      expense_ratio         = VANGUARD_EXPENSE_RATIO,
                      tax_benefit           = 0.),
             Scenario(name                  = 'MD with Y10 rollover',
                      starting_investment   = 0.,
                      annual_investment     = 2500.,
                      expense_ratio         = MD_EXPENSE_RATIO,
                      tax_benefit           = MD_STATE_TAX_2014['Couple']['$3,000'] \
                                              + MD_COUNTY_TAX_2014['Montgomery County'],
                      rollover_tax_benefit  = 0.,
                      rollover_expense_ratio = VANGUARD_EXPENSE_RATIO,
                      rollover_year         = 9)]

# import historical market index data from csv file
with open(HISTORICAL_DATA, 'rb') as csvfile:
    rows = csv.DictReader(csvfile)
    historical_performances = numpy.array([float(row[INDEX]) for row in rows if row[INDEX] <> ''])
    
print '                       Number of Years: {NUM_OF_YEARS} years\n'\
      '                 Historical Index Used: {INDEX}\n'\
      '                         Calculating... {SIMULATIONS:,} simulations\n'\
      ''.format(**locals())

for scenario in SCENARIOS:
    scenario.results = numpy.empty(SIMULATIONS)
    scenario.results.fill(scenario.starting_investment)
    scenario.carryover_deductible = scenario.starting_investment
for year in range(NUM_OF_YEARS):
    indices = numpy.random.randint(len(historical_performances), size=SIMULATIONS)
    performances = historical_performances[indices]
    for scenario in SCENARIOS:
        scenario.results += scenario.annual_investment
        scenario.results *= 1 + performances-scenario.expense_ratio
        # now calculate and reinvest the tax benefit (reinvestment is unrealistic)
        scenario.carryover_deductible += scenario.annual_investment
        if scenario.carryover_deductible > 2500:
            deductible = 2500.
        else:
            deductible = scenario.carryover_deductible
        scenario.carryover_deductible -= deductible
        scenario.results += deductible*scenario.tax_benefit
        if scenario.rollover_year is not None and year == scenario.rollover_year:
            # simulate rollover into less expensive plan
            scenario.expense_ratio = scenario.rollover_expense_ratio
            scenario.tax_benefit = scenario.rollover_tax_benefit
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