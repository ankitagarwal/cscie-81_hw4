import matplotlib.pyplot as plt
from sys import argv
from os import listdir, remove
from os.path import isfile, join
import numbers
import numpy as np
import scipy as sp
from scipy.stats import f


conversions = {'a':0, 'b':1, 'c':2, 'd':3,'e':4}
window = 5
baselineSize = 50
#Currently using the standard .05 alpha level, which gives us a
#high degree of confidence that a change is valid
#We are dividing by 2 for the two tailed test
confidence = .95
alphaVar = (1-confidence) / 2
  



#This cleaning function strips out any extra whitespace, 
#converts any letters to numbers (see paper for explanation),
#and converts all string objects to floats for calculation
def safeGet(fileObj):
	line = fileObj.readline().strip()
	if line == "":
		return line
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
	global alphaVar
	global baselineSize
	
	buffered = []
	for i in range(window):
		line = safeGet(fileCon)
		if line == "":
			raise EOFError("No samples, or too few samples in file")
		buffered.append(line)
	windowMeas = {'stdDev':np.std(buffered), 'mean':np.mean(buffered), 'var':np.var(buffered), 'sem':sp.stats.sem(buffered, ddof=0)}
	pValue = 0.0
	
	#A variance of 0 means we can't perform the F-test
	if(windowMeas['var'] != 0):
		#variance has increased
		if(windowMeas['var'] > measurements['var']):
			pValue = sp.stats.f.sf((windowMeas['var'] / measurements['var']), window - 1, baselineSize - 1)
		#variance has decreased
		else:
			pValue = sp.stats.f.sf((measurements['var'] / windowMeas['var']), baselineSize - 1, window - 1)
		if  pValue < alphaVar:
			print("Variance ", end="")
			return True


	#Calculate confidence in the mean
	stdErrDiff = sp.sqrt(windowMeas['sem']**2+measurements['sem']**2)
	meanInterval = sp.stats.norm.interval(confidence)*stdErrDiff
	print(meanInterval)
	

#	else:
		#in the end this should be removed, but right now it could help tell
		#us how big the window should be. The larger the window the less likely
		#it is that we will happen to get an buffered of all 1 number. 
#		print("The variance of this window is 0")

	#Calculate cumulative probability density
	#Now that we have the necessary data measurements, we can compare them
	if windowMeas['stdDev'] > measurements['stdDev']*1.2:
		print("Mean ", end="")
		return True


#This is an attempt to narrow down where the variance changes.
#It is not very precise, but the forums said we just needed to estimate the 
#location of the line for variance. 
#the mean argument should always = np.mean(buffered) 
#It is a recursive creation that takes the line that getWindow's fileCon (line) is
#beginning on, the buffered array thing (divideThis), and weather the variance has increased
#or decreased (varianceUp) as its arguments. line = int, divideThis = [], and 
#varianceUp = boolean. The idea is to divide the divideThis in half and take half
#with the larger (if varianceUp = True) or the smaller (if varianceUp = False)
#variance and keep on dividing until we reach a point where we can't divide up
#any more  	
def getLine(divideThis, line, varianceUp, mean):
	divideThis1 = []
	divideThis2 = []
	for i in range(lent(divideThis)):
		if (i <= len(divideThis)):
			divideThis1.append(divideThis[i])
		else:
			divideThis2.append(divideThis[i])
		
	if len(divideThis) <= 2:
		var1 = (divideThis1[0] - mean) ^ 2
		var2 = (divideThis2[0] - mean) ^ 2
		#the variance has increased 
		if varianceUp:
			if var1 > var2:
				return line
			else:
				return line + 1
		#varianceUp is false so we want the line that the lower variance is on
		else:
			if var1 < var2:
				return line
			else:
				return line + 1
	#find which half is higher
	if varianceUp:		
		if np.var(divideThis1) > np.var(divideThis2):
			getLine(divideThis1, line, varianceUp, mean)
		else:
			getLine(divideThis2, line + len(divideThis1) - 1, varianceUp, mean)
	#Or find which half is lower
	else:
		if np.var(divideThis1) < np.var(divideThis2):
			getLine(divideThis1, line, varianceUp, mean)
		else:
			getLine(divideThis2, line + lent(divideThis1) - 1, varianceUp, mean)
		


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
	#TESTING
	fileCon = open(directory+'/'+txtFile, 'r')
	allData = []
	line = safeGet(fileCon)
	while line != "":
		allData.append(line)
		line = safeGet(fileCon)
	plt.plot(allData)
	plt.show()
	fileCon.close()
	#TESTING

	fileCon = open(directory+'/'+txtFile, 'r')
	baseline = []
	#We are assuming, given the assignment guidelines, that the first
	#50 samples can be used for baseline measurements
	for i in range(baselineSize+1):
		line = safeGet(fileCon)
		baseline.append(line)

	#added variance to measurements
	measurements = {'mean':np.mean(baseline), 'stdDev':np.std(baseline), 'var':np.var(baseline), 'sem':sp.stats.sem(baseline, ddof=0)}
	
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
