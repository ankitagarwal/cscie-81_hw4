import csv
import itertools
import sys
from itertools import zip_longest

with open('winequality-red.csv', 'r') as csvfile:
	# Read all Tab-delimited rows from stdin.
	tsv_reader = csv.reader(csvfile, delimiter=',')
	all_data = list(tsv_reader)

	# Transpose it.
	all_data = list(zip_longest(*all_data, fillvalue=''))


with open('winequality-redT.csv', 'w') as output:
	# Write it back out.
	tsv_writer = csv.writer(output, delimiter=',')
	for row in all_data:
	    tsv_writer.writerow(row) 

