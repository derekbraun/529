#!/usr/local/bin/python -u

'''
    This is the model for simulating various 529 plan scenarios.
    
    The 'beauty' of the model is it captures the variability in outcomes by
    sampling from historical market performances over many thousands of
    simulations. This nonparametric approach captures stochasticity much better
    than parametric summary statistics would. Comment: I am always surprised
    that I don't see nonparametric approaches used more often given how
    powerful computers have become, which historically was the driving
    motivation for parametric approaches.
    
    All of the simulations should be run using the same random number matrix, 
    to allow for more precise comparison of various scenarios with a smaller 
    number of simulations. The random number matrix provides a list of indices
    for looking up historical performances. By using the same random number 
    matrix for all scenarios, all the scenarios will be using the exact 
    same historical years, which makes the experiments more tightly controlled
    i.e. 'noise factors' are eliminated. A fair analogy would be the greater
    statistical power that paired t-tests have over unpaired t-tests.
    
    Scenario parameters are passed to this model by a separate run file. 
    One can create many different run files, with different 
    parameters/scenarios, if so desired.

    We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/
    Following the line wrapping specification is sometimes difficult.
'''

import os.path
import numpy
import csv

SIMULATIONS         = 100000
MAX_NUM_OF_YEARS    = 50
PATH                = os.path.dirname(__file__)
HISTORICAL_DATAFILE = os.path.join(PATH, 'historical_data.csv')


# Define tax lookup tables (LUTs). These are provided for convenience when
# specifying models.

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


# load historical market data into memory

with open(HISTORICAL_DATAFILE, 'rb') as csvfile:
    table = [row for row in csv.reader(csvfile)]
    HISTORICAL_DATA = dict()
    for i, key in enumerate(table[0]):
        HISTORICAL_DATA[key] = numpy.array([float(row[i]) for row in table[1:]])
                    
# get the length of one of the historical data lists, and use this to 
# create a numpy array
# that contains random indexes to a row on the historical data list.

length = len(HISTORICAL_DATA[HISTORICAL_DATA.keys()[0]])
RANDARRAY = [numpy.random.randint(length, size=SIMULATIONS) for i in range(MAX_NUM_OF_YEARS)]


class Scenario:
    '''
        Convenient container for all of the variables needed to define each
        scenario.
    '''
    def __init__(self, name = None, starting_investment = None, 
                 annual_investment = None, num_of_years = None,
                 index = None, expense_ratio = 0, tax_benefit_ratio = 0, 
                 rollover_year = None, rollover_expense_ratio = None,  
                 rollover_tax_benefit_ratio = 0.):
        self.name = name
        self.starting_investment = starting_investment
        self.annual_investment = annual_investment
        self.num_of_years = num_of_years
        self.index = index
        self.expense_ratio = expense_ratio
        self.tax_benefit_ratio = tax_benefit_ratio
        self.rollover_year = rollover_year
        self.rollover_expense_ratio = rollover_expense_ratio
        self.rollover_tax_benefit_ratio = rollover_tax_benefit_ratio
        # check to see that all variables are properly set. If not,
        # output an informative error message.
        for attr in ['starting_investment','annual_investment','num_of_years', 'index']:
            if getattr(self, attr) is None:
                print "You need to pass a value for the '{}' parameter "\
                      "to your Scenario class.".format(attr)
                exit()
                
    def simulate(self):
        print '                              Scenario: {self.name}\n' \
              '                   Starting Investment: ${self.starting_investment:,.0f}\n'\
              '           Annual Investment into Plan: ${self.annual_investment:,.0f}\n'\
              '                       Number of Years: {self.num_of_years} years\n'\
              '                 Using Historical Data: {self.index}\n'\
              '                         Expense Ratio: {self.expense_ratio:.2%}\n'\
              '                     State Tax Benefit: {self.tax_benefit_ratio:.2%}'\
              ''.format(**locals())
        if self.rollover_year is not None:
            print '                         Rollover Year: {self.rollover_year}\n'\
                  '                Rollover Expense Ratio: {self.rollover_expense_ratio:.2%}\n'\
                  '            Rollover State Tax Benefit: {self.rollover_tax_benefit_ratio:.2%}'\
                  ''.format(**locals())
        print '                         Calculating... {:,} simulations'\
              ''.format(SIMULATIONS)
              
        principals = numpy.empty(SIMULATIONS)
        principals.fill(self.starting_investment)
        carryover_deductible = self.starting_investment
        for year in range(self.num_of_years):
            performances = HISTORICAL_DATA[self.index][RANDARRAY[year]]
            principals += self.annual_investment
            principals *= 1 + performances-self.expense_ratio
            # now calculate and reinvest the tax benefit 
            # (note: reinvestment of the tax benefit is unrealistic)
            carryover_deductible += self.annual_investment
            if carryover_deductible > 2500:
                this_yr_deductible = 2500.
            else:
                this_yr_deductible = carryover_deductible
            carryover_deductible -= this_yr_deductible
            principals += this_yr_deductible*self.tax_benefit_ratio
            if self.rollover_year is not None and year == self.rollover_year:
                # simulate rollover into less expensive plan
                self.expense_ratio = self.rollover_expense_ratio
                self.tax_benefit_ratio = self.rollover_tax_benefit_ratio

        principals.sort()
        median = principals[int(0.5*SIMULATIONS)]
        hpd_low = principals[int(0.025*SIMULATIONS)]
        hpd_high = principals[int(0.975*SIMULATIONS)]
        print '                   Median Final Amount: ${median:,.0f} '\
              '(95% HPD: ${hpd_low:,.0f} to ${hpd_high:,.0f})\n'\
              ''.format(**locals())