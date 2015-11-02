from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymysql
import requests
import re
import string
from itertools import tee, islice
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.mixture import GMM

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from play import Play
from character import Character
from scene import Scene
from line import Line



class nGramClusters:
	conn = None
	cur = None
	nMin = 2
	nMax =3

	#########
	# Open a MySQL connection. Should be triggered by the caller before running
	# the scraper, if the caller is using MySQL
	#########
	def openCon(self):
		global conn
		global cur
		conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='mysql', charset='utf8')

		cur = conn.cursor(pymysql.cursors.DictCursor)
		cur.execute("USE shakespeare")

	#########
	# Close a MySQL connection. Should be triggered by the caller after running
	# the scraper, if the caller is using MySQL
	#########
	def closeCon(self):
		global conn
		global cur
		conn.close()

	def getPlayCharacters(self, playId):
		global cur
		cur.execute("SELECT * FROM characters WHERE playId = %s", int(playId))
		characters = cur.fetchall()
		characterNames = []
		for character in characters:
			characterNames.append(character['name'].lower())
		return characterNames


	def getCharacterText(self, characterId, punctuation=False, removeCharacters=False):
		global conn
		#Do not remove stop words. While they do not necessarily convey meaning, they do convey style
		ngrams = []
		wholePlay = []
		if punctuation:
			cur.execute("SELECT * FROM sentences_cleaned_punctuation JOIN scenes ON sentences_cleaned_punctuation.sceneId = scenes.id JOIN characters ON characters.playId = scenes.playId WHERE characters.id = %s", (int(characterId)))
		else:
			cur.execute("SELECT * FROM sentences_cleaned_unsorted JOIN scenes ON sentences_cleaned_unsorted.sceneId = scenes.id JOIN characters ON characters.playId = scenes.playId WHERE characters.id = %s", (int(characterId)))
		lines = cur.fetchall()
		if removeCharacters:
			characters = self.getPlayCharacters(characterId)
			print(characters)
		for line in lines:
			wholePlay.append(line['lineText'])
		dataArr = self.getPlayTitle(line['playId'])
		dataArr.append(line['name'])
		print(dataArr)
		wholePlay = '\n'.join(wholePlay)
		if removeCharacters:
			for name in characters:
				wholePlay = wholePlay.replace(name, "")
		dataArr.append(wholePlay)
		return dataArr

	def getPlayTitle(self, playId):
		global cur
		cur.execute("SELECT * FROM plays WHERE id = %s", (int(playId)))
		play = cur.fetchone()
		return [play['title'], play['type'], play['year']]

	def getPlayText(self, playId, punctuation=False, removeCharacters=False):
		global conn
		#Do not remove stop words. While they do not necessarily convey meaning, they do convey style
		ngrams = []
		wholePlay = []
		if punctuation:
			cur.execute("SELECT * FROM sentences_cleaned_punctuation JOIN scenes ON sentences_cleaned_punctuation.sceneId = scenes.id WHERE scenes.playId = %s", (int(playId)))
		else:
			cur.execute("SELECT * FROM sentences_cleaned_unsorted JOIN scenes ON sentences_cleaned_unsorted.sceneId = scenes.id WHERE scenes.playId = %s", (int(playId)))
		lines = cur.fetchall()
		if removeCharacters:
			characters = self.getPlayCharacters(playId)
			print(characters)
		for line in lines:
			name = line['playId']
			wholePlay.append(line['lineText'])
		dataArr = self.getPlayTitle(playId)
		print(dataArr)
		wholePlay = '\n'.join(wholePlay)
		if removeCharacters:
			for name in characters:
				wholePlay = wholePlay.replace(name, "")
		dataArr.append(wholePlay)
		return dataArr

	# custom ngram analyzer function, matching only ngrams that belong to the same line
	def ngrams_per_line(self, doc):
		global nMin
		global nMax

		for ln in doc.split('\n'):
			# tokenize the input string (customize the regex as desired)
			terms = ln.split(' ')
			# loop ngram creation for every number between min and max ngram length
			for ngramLength in range(nMin, nMax+1):
				# find and return all ngrams
				# for ngram in zip(*[terms[i:] for i in range(3)]): <-- solution without a generator (works the same but has higher memory usage)
				for ngram in zip(*[islice(seq, i, len(terms)) for i, seq in enumerate(tee(terms, ngramLength))]): # <-- solution using a generator
					ngram = ' '.join(ngram)
					yield ngram

	def makeCharacterClusters(self, type, ngramMin, ngramMax):
		global nMin
		global nMax

		nMin = ngramMin
		nMax = ngramMax

		#bigrams must exist in 30% of the plays
		vectorizer = TfidfVectorizer(analyzer=self.ngrams_per_line, min_df=0.3)
		titles = []
		titleSet = []
		texts = []
		names=[]
		xPos = []
		xPosLookup = dict()
		self = nGramClusters()
		self.openCon()
		for i in range(1,1339):
			#[play['title'], play['type'], play['year']], text
			#data = self.getPlayText(i, True, False)
			data = self.getCharacterText(i, False, False)
			if data[0] not in titleSet:
				titleSet.append(data[0])
			titles.append(titleSet.index(data[0]))
			#This is used to move the character dots across the graph
			if data[0] not in xPosLookup:
				xPosLookup[data[0]] = 0
			xPosLookup[data[0]] += 1
			xPos.append(xPosLookup[data[0]])
			names.append(data[3])
			texts.append(data[4])
			#plays[title] = text


		cluster_colors = {0: '#1f77b4', 1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5:'#8c564b', 6: '#e377c2', 7:'#7f7f7f', 8:'#bcbd22', 9:'#17becf'}
		self.closeCon()
		tfidfMatrix = vectorizer.fit_transform(texts)
		silhouetteScores = dict()
		#print("FEATURE NAMES:")
		#print(vectorizer.get_feature_names())
		print("Matrix shape is:")
		print(tfidfMatrix.shape)
		for i in range(2,10):
			print(str(i)+" CLUSTERS")
			km = KMeans(n_clusters=i, n_init=30)
			labels = km.fit_predict(tfidfMatrix)
			silhouetteAvg = silhouette_score(tfidfMatrix, labels)
			silhouetteScores[i] = silhouetteAvg
			print("SILHOUETTE: ")
			print(silhouetteAvg)
			clusters = km.labels_.tolist()
			clusterDict = dict()
			for j in range(len(clusters)):
				clustId = clusters[j]
				#Iterate through the clusters and group play names
				if clustId not in clusterDict:
					clusterDict[clustId] = ""
				clusterDict[clustId] += names[j]+", "
			for k, v in clusterDict.items():
				print(str(k)+": "+str(v))

			df = pd.DataFrame(dict(x=xPos, y=titles, label=clusters, title=names))
			groups = df.groupby('label')
			fig, ax = plt.subplots(figsize=(17, 9)) # set size
			ax.margins(0.05)
			i = 0
			for name, group in groups:
				print(name)
				print(group)
				ax.plot(group.x, group.y, marker='o', linestyle='', ms=12, label=names[0], color=cluster_colors[name], mec='none')
				i += 1
			for i in range(len(df)):
				ax.text(df.ix[i]['x'], df.ix[i]['y'], df.ix[i]['title'], size=8,rotation='vertical') 
				#There's probably a more pythonic way of doing this...
			y = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,6,17,18,19,20,21,22,23,2,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39]
			yticks = list(titleSet)
			plt.yticks(y, yticks, rotation='horizontal')
			plt.show()

		print(silhouetteScores)

	def find_outliers(self, centroids, labels, tfidfMatrix):
	# Let us find 5 points which are furthest from their centroid.
		outliers = np.array([[0, 0],[0, 0],[0, 0],[0, 0],[0, 0]])
		#centroids = km.cluster_centers_
		for index, point in enumerate(tfidfMatrix):
			dist = np.linalg.norm(point - centroids[labels[index]])
			print("Index: "+str(index)+" distance: "+str(dist))
			min_dist = 500000000
			min_index = -1
			for out_index, outlier in enumerate(outliers):
				if outlier[1] < min_dist:
					min_dist = outlier[1]
					min_index = out_index
			if (dist > min_dist):
				outliers = np.delete(outliers, min_index, axis=0)
				outliers = np.insert(outliers, 4, [index, dist], axis=0)
		for outlier in outliers:
			print("OUTLIER!")
			print(outlier)
			#plt.scatter(first[outlier[0]], second[outlier[0]], c='blue', marker='x', s=50)


	def makeClusters(self, clusterType, ngramMin, ngramMax, withPunctuation=False, removeCharacterNames=False):
		global nMin
		global nMax

		nMin = ngramMin
		nMax = ngramMax
		
		#bigrams must exist in 30% of the plays
		vectorizer = TfidfVectorizer(analyzer=self.ngrams_per_line, ngram_range=(2,2), min_df=0.3)
		titles = []
		genres = []
		genrePos = {'COMEDY': 1, 'TRAGEDY': 2, 'HISTORY': 3, 'POETRY': 4}
		years = []
		texts = []
		self = nGramClusters()
		self.openCon()
		for i in range(1,40):
			#[play['title'], play['type'], play['year']], text
			data = self.getPlayText(i, withPunctuation, removeCharacterNames)
			titles.append(data[0])
			years.append(data[2])
			genres.append(genrePos[data[1]])
			texts.append(data[3])

		#If plays are in the same year and genre (this happens
		#in a couple cases, this will offset them a little to make
		#The distinction in the final chart clear)
		for i in range(len(years)):
			for j in range(i+1, len(years)):
				if years[i] == years[j] and genres[i] == genres[j]:
					genres[j] = genres[j] + .25
					years[j] = years[j] + .25



		cluster_colors = {0: '#1f77b4', 1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5:'#8c564b', 6: '#e377c2', 7:'#7f7f7f', 8:'#bcbd22', 9:'#17becf'}
		self.closeCon()
		tfidfMatrix = vectorizer.fit_transform(texts)
		silhouetteScores = dict()

		print("Matrix shape is:")
		print(tfidfMatrix.shape)
		for i in range(2,10):
			print(str(i)+" CLUSTERS")
			if clusterType == "km":
				print("Running KMeans")
				km = KMeans(n_clusters=i, n_init=30)
				labels = km.fit_predict(tfidfMatrix)
				clusters = km.labels_.tolist()
				silhouetteAvg = silhouette_score(tfidfMatrix, labels)
				centroids = km.cluster_centers_
				self.find_outliers(centroids, labels, tfidfMatrix.toarray())
			else:
				print("Running GMM")
				gmm = GMM(n_components=i)
				labels = gmm.fit(tfidfMatrix.toarray())
				clusters = gmm.predict(tfidfMatrix.toarray())
				silhouetteAvg = silhouette_score(tfidfMatrix.toarray(), clusters)

			silhouetteScores[i] = silhouetteAvg
			print("SILHOUETTE: ")
			print(silhouetteAvg)
			
			clusterDict = dict()
			for j in range(len(clusters)):
				clustId = clusters[j]
				#Iterate through the clusters and group play names
				if clustId not in clusterDict:
					clusterDict[clustId] = ""
				clusterDict[clustId] += titles[j]+", "
			for k, v in clusterDict.items():
				print(str(k)+": "+str(v))


			firstYear = min(years)
			lastYear = max(years)
			df = pd.DataFrame(dict(x=years, y=genres, label=clusters, title=titles))
			groups = df.groupby('label')
			fig, ax = plt.subplots(figsize=(17, 9)) # set size
			ax.margins(0.05)
			j = 0
			for name, group in groups:
				#print(name)
				#print(group)
				ax.plot(group.x, group.y, marker='o', linestyle='', ms=12, label=titles[0], color=cluster_colors[name], mec='none')
				j += 1
			for j in range(len(df)):
				ax.text(df.ix[j]['x']+.15, df.ix[j]['y'], df.ix[j]['title'], size=10,rotation='vertical') 
			y = [1, 2, 3, 4]
			yticks = ['COMEDY', 'TRAGEDY', 'HISTORY', 'POETRY']
			plt.yticks(y, yticks, rotation='horizontal')
			ngramText = ""
			if nMin != nMax:
				ngramText = str(nMin)+"-"+str(nMax)
			else:
				ngramText = str(nMin)
			ngramText = ngramText+"grams"
			figureTitle = "All Plays, "+str(ngramText)+" "+str(clusterType)
			if withPunctuation:
				figureTitle = figureTitle+" with Punctuation"
			if removeCharacterNames:
				figureTitle = figureTitle+" character names removed"
			figureTitle = figureTitle+" "+str(i)+" clusters"
			plt.suptitle(figureTitle, fontsize=20)
			if i == 0:
				plt.show()

		print(silhouetteScores)

ngrammer = nGramClusters()
ngrammer.makeClusters("km", 1, 1, True, True)
#ngrammer.makeCharacterClusters()

