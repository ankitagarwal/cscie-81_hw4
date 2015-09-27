import matplotlib.pyplot as plt
from sys import argv
from os import listdir, remove
from os.path import isfile, join
import numbers
import numpy as np
import scipy as sp
from scipy.stats import f


window = 10
baselineSize = 50
#Currently using the standard .05 alpha level, which gives us a
#high degree of confidence that a change is valid
#We are dividing by 2 for the two tailed test
confidence = .95
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
	pValue = sp.stats.chi2.ppf(confidence, window-1)
	chiSquared = sp.stats.chi2_contingency(np.array([bufferVals['freq'], baselineVals['freq']]))[0]
	if chiSquared > pValue:
		print("Chi square frequency change detected! p-value: "+str(pValue)+" chiSquared: "+str(chiSquared))
		return True
	return False


def meanVarianceTest(bufferVals, baselineVals):
	global window
	global alpha
	global baselineSize
	
	#VARIANCE TEST
	#A variance of 0 means we can't perform the F-test
	if bufferVals['var'] != 0:
		#variance has increased
		if(bufferVals['var'] > bufferVals['var']):
			pValue = sp.stats.f.sf((bufferVals['var'] / baselineVals['var']), window - 1, baselineSize - 1)
		#variance has decreased
		else:
			pValue = sp.stats.f.sf((baselineVals['var'] / bufferVals['var']), baselineSize - 1, window - 1)
		if  pValue < alpha:
			print("Variance ", end="")
			print("Variance has changed")
			return True


	#MEAN TEST

	#This should be a very rare case, but I want to try and handle it in a sensical-ish way
	if bufferVals['stdDev'] == 0:
		print("Standard deviation of samples is 0!")
		confidence = sp.stats.t.ppf(alpha/2, 9)
		if np.absolute(baselineVals['mean'] - bufferVals['mean']) < ((baselineVals['stdDev']/sp.sqrt(bufferSize))*confidence):
			return True
		else:
			return False

	#Perform a t test of the small number of samples (We're assuming the window is <30, 
	#However, this will still work for larger windows. To determine if the mean is within
	#Acceptable parameters
	tStat = (baselineVals['mean']-bufferVals['mean'])/(bufferVals['stdDev']/sp.sqrt(window))
	#This will be the low half of the confidence interval, e.g. -2.262 for 95%
	confidence = sp.stats.t.ppf(alpha/2, 9)
	if tStat < confidence or tStat > -confidence:
		print("Baseline changed")
		return True
	else:
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
		frequencies = buildFrequencies(buffered, measurements['chars'])
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
#Get each file in the provided directory
for txtFile in files:
	print("---------------------")
	print(txtFile)
	outputLine = txtFile+'\t'
	########TESTING
	fileCon = open(directory+'/'+txtFile, 'r')
	allData = []
	line = numericGet(fileCon)
	while line != "":
		allData.append(line)
		line = numericGet(fileCon)
	plt.plot(allData)
	#plt.show()
	fileCon.close()
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
		measurements = {'freq':buildFrequencies(baseline), 'chars':list(set(baseline))}


	#scale = measurements['stdDev']/sp.sqrt(baselineSize)
	#interval = stats.norm.interval(confidence, loc=measurements['mean'], scale=scale)
	#measurements.append['interval':interval]
	lineCount = baselineSize
	try:
		while not getWindow(fileCon, measurements):
			lineCount += window
		print("change found on line "+str(lineCount))
		outputLine += str(lineCount)+'\n'
	except EOFError:
		print("No changes found in file")
		outputLine += '-1\n'

	output.write(outputLine)
	fileCon.close()

output.close()
