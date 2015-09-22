import matplotlib.pyplot as plt
from sys import argv
from os import listdir, remove
from os.path import isfile, join
import numbers
import numpy as np

conversions = {'a':0, 'b':1, 'c':2, 'd':3,'e':4}
window = 10
baselineSize = 50


#This cleaning function strips out any extra whitespace, 
#converts any letters to numbers (see paper for explanation),
#and converts all string objects to floats for calculation
def clean(line):
	line = line.strip()
	global conversions
	if line in conversions:
		line = conversions[line]
	return float(line)


#Takes as arguments a file object and a dict of 
#baseline measurements (std deviation, mean, see usage below)
#gets the next window of samples and determines if they 
#are acceptably close to the measurements given
#If the next "window" of samples is within range, a False is returned,
#if they are outside range, True is returned (it is up to the caller to
#keep track of which line in the file has been reached, based on the 
#global "window" variable)
#If the end of the file is reached, the file object is set to 
#None, so it is easy for the caller to tell if the end of the
#file has been reached or not
def getWindow(fileCon, measurements):
	global window
	buffered = []
	for i in range(window):
		line = fileCon.readline()
		if line == "":
			raise EOFError("No samples, or too few samples in file")
		buffered.append(clean(line))
	windowsMeas = {'stdDev':np.std(buffered), 'mean':np.mean(buffered)}
	
	#Now that we have the necessary data measurements, we can compare them
	if windowsMeas['stdDev'] > measurements['stdDev']*1.2:
		return True

	


directory = argv[1]
if isfile('output.txt'):
	remove('output.txt')
output = open('output.txt', 'a')
output.truncate()
files = [ f for f in listdir(directory) if isfile(join(directory,f)) ]
#Get each file in the provided directory
for txtFile in files:
	print(txtFile)
	outputLine = txtFile+'\t'
	fileCon = open(directory+'/'+txtFile, 'r')
	baseline = []
	#We are assuming, given the assignment guidelines, that the first
	#50 samples can be used for baseline measurements
	for i in range(baselineSize+1):
		baseline.append(clean(fileCon.readline()))

	measurements = {'mean':np.mean(baseline), 'stdDev':np.std(baseline)}
	lineCount = baselineSize
	try:
		while not getWindow(fileCon, measurements):
			lineCount += window
		print("Change found on line "+str(lineCount))
		outputLine += str(lineCount)+'\n'
	except EOFError:
		print("No changes found in file")
		outputLine += '-1\n'

	output.write(outputLine)
	fileCon.close()

output.close()
