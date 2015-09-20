import matplotlib.pyplot as plt
from sys import argv
from os import listdir
from os.path import isfile, join
import numbers
import numpy as np

conversions = {'a':0, 'b':1, 'c':2, 'd':3,'e':4}
window = 10

def clean(line):
	line = line.strip()
	global conversions
	if conversions[line] is not None:
		line = conversions[line]


def getWindow(fileCon, stdDeviation):
	global window
	buffered = []
	for i in range(window):
		line = fileCon.readline()
		if line == "":
			fileCon = None
			return False
		buffered.append(clean(line))
	windowsStdDeviation = np.std(buffered)
	#windowsMean = np.mean(buffered)
	if windowsStdDeviation > stdDeviation*1.5:
		return True

	


directory = argv[1]
ouput = open('output.txt', 'a')
files = [ f for f in listdir(directory) if isfile(join(directory,f)) ]
#print(files)
for txtFile in files:
	f = open(directory+'/'+txtFile, 'r')
	baseline = []
	#doing some baseline measurin'
	while i in range(50):
		baseline.append(clean(f.readline())
		i += 1

	stdDeviation = np.std(baseline)
	line = f.readline()
	while fileCon is not None:
		if getWindow(fileCon, stdDeviaton):
			fileCon.tell()
			print("CHAHAHHANGNGNNES")





		



	#print(dataArray[0])
	#if dataArray[0] != 'a' and dataArray[0] != 'b':
	#	dataArray = list(filter(None, dataArray))
	#	dataArray = [float(x) for x in dataArray]
		#print(dataArray)
		#plt.plot(dataArray)
		#plt.ylabel('some numbers')
		#plt.show()
	#	print(np.std(dataArray[0:49]))
	#write a line to output
#window = 10

#for char in data:
