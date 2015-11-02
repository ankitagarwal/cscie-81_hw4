from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymysql
import requests
import re
import string

from play import Play
from character import Character
from scene import Scene
from line import Line
from config import *

class ShakespeareScraper:
	conn = None
	cur = None
	session = None
	headers = None

	def __init__(self):
		global conn
		global cur
		global session
		global headers

	#########
	# Open a MySQL connection. Should be triggered by the caller before running
	# the scraper, if the caller is using MySQL
	#########
	def openCon(self):
		global conn
		global cur
		conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db='mysql', charset='utf8')

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

	def getPage(self, url):
		global session
		global headers

		session = requests.Session()
		headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}

		print("Retrieving URL:\n"+url)
		try:
			req = session.get(url, headers=headers)
		except requests.exceptions.RequestException:
			return None
		bsObj = BeautifulSoup(req.text)
		#Removing the italicized direction text in the scripts to make things a little cleaner
		[x.extract() for x in bsObj.findAll('em')]

		return bsObj

	def strip(self, myString):
		myString = myString.strip(string.whitespace+"\""+"'")
		return myString

	#Stores character to database, if the character does not
	#Already exist
	def storeCharacter(self, character):
		global conn
		global cur
		cur.execute("SELECT * FROM characters WHERE name = %s AND playId = %s", (character.name, int(character.play.id)))
		if cur.rowcount == 0:
			try:
				cur.execute("INSERT INTO characters (playId, name) VALUES(%s, %s)", (int(character.play.id), character.name))
			except:
				print("ERROR: Could not store character")
			try:
				conn.commit()
				character.id = conn.insert_id()
				return character
			except:
				conn.rollback()

		else:
			character.id = cur.fetchone()['id']
			return character


	#Stores play to database, if the play does not already exist
	def storePlay(self, play):
		global conn
		global cur
		cur.execute("SELECT * FROM plays WHERE urlkey = %s", (play.urlkey))

		if cur.rowcount == 0:
			try:
				cur.execute("INSERT INTO plays (title, urlkey, type) VALUES(%s, %s, %s)", (play.title, play.urlkey, play.type))
			except:
				print("ERROR: Could not store play")
			try:
				conn.commit()
				play.id = conn.insert_id()
				return play
			except:
				conn.rollback()
		else:

			play.id = cur.fetchone()['id']
			return play


	#Stores scene to database, if the scene does not already exist
	def storeScene(self, scene):
		global conn
		global cur

		cur.execute("SELECT * FROM scenes WHERE playId = %s AND scene = %s AND act= %s", (int(scene.play.id), int(scene.scene), int(scene.act)))
		if cur.rowcount == 0:
			try:
				cur.execute("INSERT INTO scenes (playId, act, scene, title) VALUES(%s, %s, %s, %s)", (int(scene.play.id), int(scene.act), int(scene.scene), scene.title))
			except:
				print("ERROR: Could not store scene")
			try:
				conn.commit()
				scene.id = conn.insert_id()
				return scene
			except:
				conn.rollback()
		else:
			print("Scene exists")
			scene.id = cur.fetchone()['id']
			return scene

	#Stores line to database if line does not already exist
	#Note: The "lines" table is actually called "words" because lins is a reserved word. 
	def storeLine(self, line):
		global conn
		global cur
		try:
			cur.execute("INSERT INTO words (sceneId, characterId, lineText) VALUES(%s, %s, %s)", (int(line.scene.id), int(line.character.id), line.lineText))
		except:
			print("ERROR: Could not store line")
		try:
			conn.commit()
			line.id = conn.insert_id()
			return line
		except:
			conn.rollback()


	#There's probably a better way to do this, but, if a 
	#character exists in a list (by name), return it
	#If not, return None (used by getScene for caching)
	def characterExists(self, charList, name):
		for character in charList:
			if character.name == name:
				return character
		return None

	def getScene(self, url, scene):
		print("ACT "+str(scene.act)+" SCENE "+str(scene.scene))
		characters = []
		bsObj = self.getPage("http://shakespeare.mit.edu/"+scene.play.urlkey+"/"+url)
		if bsObj.h3 is not None:
			title = bsObj.h3.get_text()
			scene.title = self.strip(title)
		scene = self.storeScene(scene)
		quotes = bsObj.findAll("a", {"name":re.compile("^(speech)[0-9]*")})
		for quote in quotes:
			name = self.strip(quote.get_text())
			character = self.characterExists(characters, name)
			if character is None:
				character = Character(None, scene.play, name)
				character = self.storeCharacter(character)
				characters.append(character)

			#Get the current object we are looking at in order to get the sibling, which is the text
			#Spoken the by character in the "quote" tag
			text = bsObj.find("a",{"name":quote.attrs["name"]}).find_next_sibling().get_text()
			line = Line(None, scene, character, self.strip(text))
			self.storeLine(line)


	def scrapePlay(self, playLink, playType):
		title = self.strip(playLink.get_text())
		print("PLAY: "+str(title)+" a "+playType)
		play = Play(None, title, playType)
		url = playLink.attrs['href']
		playKey = url.split("/")[0]
		play.urlkey = playKey
		play = self.storePlay(play)

		scenes = self.getPage("http://shakespeare.mit.edu/"+url)
		links = scenes.findAll("a", href=re.compile("^("+playKey+")\.[0-9]\.[0-9]\.(html)"))
		for link in links:
			url = link.attrs["href"]
			urlSplit = url.split(".")
			scene = Scene(None, play, urlSplit[1], urlSplit[2])
			self.getScene(url, scene)
		
	def sonnetScraper(self):
		home = self.getPage("http://shakespeare.mit.edu/Poetry/sonnets.html")
		sonnets = home.dl.findAll("dt")
		play = Play(38, "Sonnets", "Poetry", "POETRY")
		character = Character(1337, play, "SONNETS")
		i = 1
		for sonnetListing in sonnets:
			url = "http://shakespeare.mit.edu/Poetry/"+sonnetListing.a.attrs['href']
			page = self.getPage(url)
			print(page.h1.get_text())
			scene = Scene(None, play, 1, i, page.h1.get_text())
			self.storeScene(scene)
			line = Line(None, scene, character, page.blockquote.get_text())
			sonnet = self.storeLine(line)
			i = i+1

	def getPlays(self):
		home = self.getPage("http://shakespeare.mit.edu/")
		table = home.find("table",{"align":"center"})
		#Second row contains plays
		row = table.findAll("tr")[1]
		columns = row.findAll("td")
		comedies = columns[0].findAll("a")
		histories = columns[1].findAll("a")
		tragedies = columns[2].findAll("a")
		poetry = columns[3].findAll("a")

		for comedy in comedies:
			self.getPlay(comedy, "COMEDY")

		for history in histories:
			self.getPlay(history, "HISTORY")

		for tragedy in tragedies:
			self.getPlay(tragedy, "TRAGEDY")

		#for poem in poetry:
		#	self.getPlay(poem, "POEM")


crawler = ShakespeareScraper()
crawler.openCon()
crawler.sonnetScraper()
#crawler.getPlays()
crawler.closeCon()
