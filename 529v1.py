#!/usr/local/bin/python -u

'''
    This one-off script calculates the average difference between two 
    scenarios. The 'beauty' of the program is it samples from a table of
    historical stock market performances, to capture the year-to-year
    variance in stock market performance.
    
    All parameters are set by changing global variables.
    
    The original script examined two refinance situations but I quickly
    repurposed this script to examine your 529 plan question.
    
    The final output originally included a histogram generated by matplotlib
    but this part was broken, I didn't try to repair it.

    Apologies: I have not always followed PEP 8
    http://legacy.python.org/dev/peps/pep-0008/
'''


HISTORICAL_MARKET_DATA = './historical_market_index_data.csv'
OUTFILENAME = '/Users/derek/Desktop/hist.pdf' 
INDEX = 'Wilshire_5000'     # choose the index you want to 
                            # use for the simulation. Options 
                            # are 'DJIA' or 'Wilshire_5000'
SIMULATIONS         = 100000
NUM_OF_YEARS        = 18
ANNUAL_INVESTMENT   = 2500.
PLAN_1_LOAD         = 0.0088
PLAN_1_BENEFIT      = 0.0475
PLAN_2_LOAD         = 0.0019
PLAN_2_BENEFIT      = 0

import random
import csv

# Import historical market index data from csv file
f = open(HISTORICAL_MARKET_DATA, 'rb')
csv_data = csv.reader(f)
indices = csv_data.next()
historical_data = {}
for index in indices:
    historical_data[index] = []
for row in csv_data:
    for i, index in enumerate(indices):
        if row[i] <> '':
            historical_data[index].append(row[i])

print ' Historical Index Used: {INDEX}'.format(**locals())
print '         Calculating... {SIMULATIONS:,} simulations.'.format(**locals())
results = []
for i in range(SIMULATIONS):
    # build performance list
    market_performances = []
    for year in range(NUM_OF_YEARS):
        market_performances.append(random.choice(historical_data[INDEX]))
        
    nest_egg1 = nest_egg2 = 0
    for market_performance in market_performances:
        nest_egg1 += nest_egg1*(float(market_performance) - PLAN_1_LOAD)
        nest_egg1 += (1 + PLAN_1_BENEFIT) * ANNUAL_INVESTMENT
        
        nest_egg2 += nest_egg2*(float(market_performance) - PLAN_2_LOAD)
        nest_egg2 += (1 + PLAN_2_BENEFIT) * ANNUAL_INVESTMENT
            
    results.append(nest_egg2-nest_egg1)
results.sort()

for i, result in enumerate(results):
    if result > 0:
        likelihood_of_breaking_even = 1-i/float(len(results))
        break
        
print '                Mean Difference: ${:,.0f}'.format(sum(results)/len(results))
print '                  95% HPD range: ${:,.0f} to ${:,.0f}'.format(results[int(0.025*SIMULATIONS)],results[int(0.975*SIMULATIONS)])
print 'Likelihood that Plan 2 > Plan 1: {:.1%}'.format(likelihood_of_breaking_even)