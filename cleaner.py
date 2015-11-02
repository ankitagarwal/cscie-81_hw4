import string
from line import Line
import pymysql
from config import *

#########
# Open a MySQL connection. Should be triggered by the caller before running
# the scraper, if the caller is using MySQL
#########
def openCon():
	conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db='mysql', charset='utf8')

	cur = conn.cursor(pymysql.cursors.DictCursor)
	cur.execute("USE shakespeare")
	return conn, cur

#########
# Close a MySQL connection. Should be triggered by the caller after running
# the scraper, if the caller is using MySQL
#########
def closeCon(conn):
	conn.close()

def makeLine(lineData):
	line = Line(lineData['id'], lineData['sceneId'], lineData['characterId'], lineData['lineText'])
	return line

#Stores line to database if line does not already exist
#Note: The "lines" table is actually called "words" because lins is a reserved word. 
def getLines(cur):
	try:
		cur.execute("SELECT * FROM sentences")
		lines = cur.fetchall()
	except:
		print("ERROR: Could not get data")

	return lines

def storeLine(line, cur, conn):
	try:
		cur.execute("INSERT INTO sentences_cleaned_unsorted (id, sceneId, characterId, lineText) VALUES(%s, %s, %s, %s)", (int(line.id), int(line.scene), int(line.character), line.lineText))
	except:
		print("ERROR: Could not store line")
	try:
		conn.commit()
		line.id = conn.insert_id()
		return line
	except:
		conn.rollback()

def storeLineWithPunctuation(line, cur, conn):
	try:
		cur.execute("INSERT INTO sentences_cleaned_punctuation(id, sceneId, characterId, lineText) VALUES(%s, %s, %s, %s)", (int(line.id), int(line.scene), int(line.character), line.lineText))
	except:
		print("ERROR: Could not store line")
	try:
		conn.commit()
		line.id = conn.insert_id()
		return line
	except:
		conn.rollback()

def getCleanLines(cur):
	try:
		cur.execute("SELECT * FROM words_cleaned")
		lines = cur.fetchall()
		return lines
	except:
		print("ERROR: Could not get data")

def storeWord(cur, conn, word, frequency):
	try:
		print("INSERT INTO words (word, frequency) VALUES ('"+word+"', "+str(frequency)+")")
		cur.execute("INSERT INTO words (word, frequency) VALUES (%s, %s);", (word, int(frequency)))
		conn.commit()
	except:
		print("Could not store word")

def saveALotOfWords(cur, conn, words):
	for word, frequency in words.items():
		storeWord(cur, conn, word, frequency)

def cleanAllLines():
	conn, cur = openCon()

	lines = getLines(cur)
	for lineData in lines:
		line = makeLine(lineData)
		allText = line.lineText
		allText = allText.replace("'", "")
		allText = allText.lower()
		for punctuation in string.punctuation:
			allText = allText.replace(punctuation, ' '+punctuation+' ')
		textArray = allText.split()
		line.lineText = ' '.join(textArray)
		print(line.lineText)
		storeLineWithPunctuation(line, cur, conn)

	closeCon(conn)

def findWords():
	words = dict()
	conn, cur = openCon()

	lines = getCleanLines(cur)
	print("Number of lines:")
	print(len(lines))
	lines = [x['lineText'] for x in lines]
	for line in lines:
		lineArr = line.split(",")
		for word in lineArr:
			if word in words:
				words[word] += 1
			else:
				words[word] = 1

	print(words)
	print("Size is: ")
	print(len(words))
	saveALotOfWords(cur, conn, words)
	closeCon(conn)

cleanAllLines()

#findWords()
