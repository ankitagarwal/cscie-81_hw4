#import matplotlib.pyplot as plt
from sys import argv
from os import listdir, remove
from os.path import isfile, join
import numbers
import numpy as np
import scipy as sp
import scipy.stats


window = 10
baselineSize = 50
chiBuffer = []
chiBufferScale = 3
#Currently using the standard .05 alpha level, which gives us a
#high degree of confidence that a change is valid
#We are dividing by 2 for the two tailed test
confidence = .98
alpha = (1-confidence) / 2
  
conversions = {'a':1, 'b':2, 'c':3, 'd':4, 'e':5}


def isnumeric(var):
	try:
		float(var)
		return True
	except:
		return False

#Testing purposes only
def numericGet(fileObj):
	global conversions
	line = fileObj.readline().strip()
	if line in conversions:
		return conversions[line]
	return line

#This cleaning function strips out any extra whitespace, 
#converts any letters to numbers (see paper for explanation),
#and converts all string objects to floats for calculation
def safeGet(fileObj):
	line = fileObj.readline().strip()
	return line


#Builds an array of of character frequencies found in the charArray given,
#or in the "incudeArray" (which may not be present in charArray)
def buildFrequencies(charArray, includeArr=[]):
	freq = []
	if 'a' in charArray+includeArr:
		freq.append(charArray.count('a'))
	if 'b' in charArray+includeArr:
		freq.append(charArray.count('b'))
	if 'c' in charArray+includeArr:
		freq.append(charArray.count('c'))
	if 'd' in charArray+includeArr:
		freq.append(charArray.count('d'))

	return freq

#Perform a chi square test with a set of buffer frequencies, 
#and baseline frequencies
def chiSquareTest(bufferVals, baselineVals):
	global window
	global baselineSize
# 	print(bufferVals['freq'])
	pValue = sp.stats.chisquare(bufferVals['freq'],baselineVals['freq'])[1]

	print(pValue)

	if pValue < (1-confidence):
		print(bufferVals['freq'])
		print(baselineVals['freq'])
		print("Chi square frequency change detected! p-value: "+str(pValue))
		return True
	return False


def meanVarianceTest(bufferVals, baselineVals):
	global window
	global alpha
	global baselineSize
	
	#MEAN TEST
	#This should be a very rare case, but I want to try and handle it in a sensical-ish way
	if bufferVals['stdDev'] == 0:
		print("Standard deviation of samples is 0!")
		confidence = sp.stats.t.ppf(alpha, 9)
		if np.absolute(baselineVals['mean'] - bufferVals['mean']) < ((baselineVals['stdDev']/sp.sqrt(bufferSize))*confidence):
			return True
		else:
			return False

	#Perform a t test of the small number of samples (We're assuming the window is <30, 
	#However, this will still work for larger windows. To determine if the mean is within
	#Acceptable parameters
	tStat = (baselineVals['mean']-bufferVals['mean'])/(bufferVals['stdDev']/sp.sqrt(window))
	#This will be the low half of the confidence interval, e.g. -2.262 for 95%
	confidence = sp.stats.t.ppf(alpha, 9)
	if tStat < confidence or tStat > -confidence:
		print("Baseline changed")
		return True

	
	#VARIANCE TEST
	#A variance of 0 means we can't perform the F-test
	if(baselineVals['var'] != 0):
		FValue = bufferVals['var'] / baselineVals['var']
		pValue = sp.stats.f.cdf(FValue, window - 1, baselineSize - 1)
		print(FValue)
		print(pValue)
		
		if  pValue > (1-confidence):
			print("Variance ", end = "")
			return True
# 	In the unlikely case that the baseline variance is 0 that means finding any 
# 	variance at all is a change in variance  
	else:
		if bufferVals['var'] > 0:
			print("Variance ", end = "")
			return True 
		
	return False
	
	
	

	
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
	global chiBuffer 
	
	buffered = []
	for i in range(window):
		line = safeGet(fileCon)
		if line == "":
			raise EOFError("No samples, or too few samples remaining in file")
		buffered.append(line)
	if isnumeric(buffered[0]):
		buffered = [float(x) for x in buffered]
		bufferMeasurements = {'stdDev':np.std(buffered), 'mean':np.mean(buffered), 'var':np.var(buffered)}
		return meanVarianceTest(bufferMeasurements, measurements)
	else:
		if len(chiBuffer) <= window*chiBufferScale:
			chiBuffer = chiBuffer[window:]
		chiBuffer = chiBuffer + buffered
		frequencies = buildFrequencies(chiBuffer, measurements['chars'])
		#There is a new character encountered -- not only is this a change, but we cannot
		#do a chi square test with 0 expected samples for that character, because of divide by zero errors
		if len(frequencies) > len(measurements['freq']):
			return False
		bufferMeasurements = {'freq':frequencies}
		
		return chiSquareTest(bufferMeasurements, measurements)


directory = argv[1]
if isfile('output.txt'):
	remove('output.txt')
output = open('output.txt', 'a')
output.truncate()
files = [ f for f in listdir(directory) if isfile(join(directory,f)) ]
files = sorted(files)
#Get each file in the provided directory
for txtFile in files:
	print("---------------------")
	print(txtFile)
	outputLine = txtFile+'\t'
	chiBuffer = []
	########TESTING
	#fileCon = open(directory+'/'+txtFile, 'r')
	#allData = []
	#line = numericGet(fileCon)
	#while line != "":
	#	allData.append(line)
	#	line = numericGet(fileCon)
	#plt.plot(allData)
	#plt.show()
	#fileCon.close()
	#########TESTING

	fileCon = open(directory+'/'+txtFile, 'r')
	baseline = []
	#We are assuming, given the assignment guidelines, that the first
	#50 samples can be used for baseline measurements
	for i in range(baselineSize+1):
		line = safeGet(fileCon)
		baseline.append(line)

	if isnumeric(baseline[0]):
		#Numeric values. Will do mean and variance test
		baseline = [float(x) for x in baseline]
		measurements = {'mean':np.mean(baseline), 'stdDev':np.std(baseline), 'var':np.var(baseline)}
	else:
		#alphanumeric baseline. Will do chi square test
		#Get the frequencies of each character to calculate observed and exepected values later
		#Also, get a unique set of all chars in the list, so we can make sure to grab "0 occurences"
		#for characters we may not see in every window
		chiBuffer = baseline[window*chiBufferScale:]
		measurements = {'freq':buildFrequencies(baseline), 'chars':list(set(baseline))}
	

	#scale = measurements['stdDev']/sp.sqrt(baselineSize)
	#interval = stats.norm.interval(confidence, loc=measurements['mean'], scale=scale)
	#measurements.append['interval':interval]
	lineCount = baselineSize
	try:
		while not getWindow(fileCon, measurements):
			print(lineCount)
			lineCount += window
		print("change found on line "+str(lineCount))
		outputLine += str(lineCount)+'\n'
	except EOFError:
		print("No changes found in file")
		outputLine += '-1\n'

	output.write(outputLine)
	fileCon.close()

output.close()