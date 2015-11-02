import nltk
import pymysql
import collections
from nltk.tokenize import RegexpTokenizer

from play import Play
from character import Character
from scene import Scene
from line import Line
from config import *

class featureCollector:
    conn = None
    cur = None

    def get_feature_list(self):
        return [',', '.', 'and', 'or', 'a', 'an', 'the', 'in', 'on', 'to', 'of', 'it', 'that', 'as', 'is', 'so']

    def __init__(self):
        global conn
        global cur

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

    def get_sentences(self, cleaned):
        global conn
        global cur
        if (cleaned):
            cur.execute("Select * from sentences_cleaned")
        else:
            cur.execute("Select * from sentences")
        return cur

    def get_scenes(self, cleaned):
        global conn
        global cur
        cur.execute("SET SESSION group_concat_max_len = 100000;")
        if (cleaned):
            cur.execute("Select scenes.id, COUNT(Distinct characterId) AS characterCount, GROUP_CONCAT(lineText SEPARATOR ' ') AS fullSceneText from sentences_cleaned JOIN scenes ON sentences_cleaned.sceneId = scenes.id GROUP BY scenes.id")
        else:
            cur.execute("Select scenes.id, COUNT(Distinct characterId) AS characterCount, GROUP_CONCAT(lineText SEPARATOR ' ') AS fullSceneText from sentences JOIN scenes ON sentences.sceneId = scenes.id GROUP BY scenes.id")
        return cur

    def get_plays(self, cleaned):
        global conn
        global cur
        cur.execute("SET SESSION group_concat_max_len = 1000000;")
        if (cleaned):
            cur.execute("Select plays.id, COUNT(Distinct characterId) AS characterCount, GROUP_CONCAT(lineText SEPARATOR ' ') AS fullPlayText from sentences_cleaned JOIN scenes ON sentences_cleaned.sceneId = scenes.id JOIN plays ON scenes.id = plays.id GROUP BY plays.id")
        else:
            cur.execute("Select plays.id, COUNT(Distinct characterId) AS characterCount, GROUP_CONCAT(lineText SEPARATOR ' ') AS fullPlayText from sentences JOIN scenes ON sentences.sceneId = scenes.id JOIN plays ON scenes.id = plays.id GROUP BY plays.id")
        return cur

    def collect_sentences_features(self, cleaned):
        sentences = self.get_sentences(cleaned)
        all_features = []
        for row in sentences:
            features = {}
            lineObj = Line(row['id'], row['sceneId'], row['characterId'], row['lineText'])
            tokens = nltk.word_tokenize(row['lineText'])
            wordcounts = collections.Counter(tokens)
            features['uniquewords'] = len(wordcounts)
            features['sentences'] = len(tokens)
            features['chars'] = len(lineObj.lineText)
            features['lineid'] = lineObj.id
            for element in self.get_feature_list():
                features[element] = wordcounts[element]
            all_features.append(features)
        for features in all_features:
            features = self.storeLineFeature(features, cleaned)
        return 1

    #Stores line features to database
    #Note: There are tons of reserved sentences here, hence _count is added.
    def storeLineFeature(self, features, cleaned):
        global conn
        global cur
        if cleaned:
            table = 'features_sentences_cleaned'
        else:
            table = 'features_sentences'
        try:
            cur.execute("INSERT INTO " + table + " "
                        "(lineId, chars_count, words_count, uniquewords_count, comma_count, dot_count, and_count,"
                        "or_count, a_count, an_count, the_count, in_count, on_count, to_count, of_count, it_count,"
                        "that_count, as_count, is_count, so_count) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (int(features['lineid']), int(features['chars']), int(features['sentences']), int(features['uniquewords']), int(features[',']),
                         int(features['.']), int(features['and']), int(features['or']), int(features['a']), int(features['an']),
                         int(features['the']), int(features['in']), int(features['on']), int(features['to']),
                         int(features['of']), int(features['it']), int(features['that']), int(features['as']),
                         int(features['is']), int(features['so'])))
        except:
            print("ERROR: Could not store line feature")
        try:
            conn.commit()
            features['id'] = conn.insert_id()
            return features
        except:
            print("ERROR: Could not store line feature")
            conn.rollback()

    def collect_scene_features(self, cleaned):
        scenes = self.get_scenes(cleaned)
        all_features = []
        for row in scenes:
            features = {}
            tokens = nltk.word_tokenize(row['fullSceneText'])
            wordcounts = collections.Counter(tokens)
            features['characters'] = row['characterCount']
            features['uniquewords'] = len(wordcounts)
            features['sentences'] = len(tokens)
            features['chars'] = len(row['fullSceneText'])
            features['sceneid'] = row['id']
            for element in self.get_feature_list():
                features[element] = wordcounts[element]
            all_features.append(features)
        for features in all_features:
            features = self.storeSceneFeature(features, cleaned)
        return 1

    #Stores scene features to database
    #Note: There are tons of reserved sentences here, hence _count is added.
    def storeSceneFeature(self, features, cleaned):
        global conn
        global cur
        if cleaned:
            table = 'features_scenes_cleaned'
        else:
            table = 'features_scenes'
        try:
            cur.execute("INSERT INTO " + table + " "
                        "(sceneId, character_count, chars_count, words_count, uniquewords_count, comma_count, dot_count, and_count,"
                        "or_count, a_count, an_count, the_count, in_count, on_count, to_count, of_count, it_count,"
                        "that_count, as_count, is_count, so_count) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (int(features['sceneid']), int(features['characters']), int(features['chars']), int(features['sentences']), int(features['uniquewords']), int(features[',']),
                         int(features['.']), int(features['and']), int(features['or']), int(features['a']), int(features['an']),
                         int(features['the']), int(features['in']), int(features['on']), int(features['to']),
                         int(features['of']), int(features['it']), int(features['that']), int(features['as']),
                         int(features['is']), int(features['so'])))
        except:
            print("ERROR: Could not store scene feature")
        try:
            conn.commit()
            features['id'] = conn.insert_id()
            return features
        except:
            print("ERROR: Could not store scene feature")
            conn.rollback()

    def collect_play_features(self, cleaned):
        plays = self.get_plays(cleaned)
        all_features = []
        for row in plays:
            features = {}
            tokens = nltk.word_tokenize(row['fullPlayText'])
            wordcounts = collections.Counter(tokens)
            features['characters'] = row['characterCount']
            features['uniquewords'] = len(wordcounts)
            features['sentences'] = len(tokens)
            features['chars'] = len(row['fullPlayText'])
            features['playid'] = row['id']
            for element in self.get_feature_list():
                features[element] = wordcounts[element]
            all_features.append(features)
        for features in all_features:
            features = self.storePlayFeature(features, cleaned)
        return 1

    #Stores Play features to database
    #Note: There are tons of reserved sentences here, hence _count is added.
    def storePlayFeature(self, features, cleaned):
        global conn
        global cur
        if cleaned:
            table = 'features_plays_cleaned'
        else:
            table = 'features_plays'
        try:
            cur.execute("INSERT INTO " + table + " "
                        "(playId, character_count, chars_count, words_count, uniquewords_count, comma_count, dot_count, and_count,"
                        "or_count, a_count, an_count, the_count, in_count, on_count, to_count, of_count, it_count,"
                        "that_count, as_count, is_count, so_count) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (int(features['playid']), int(features['characters']), int(features['chars']), int(features['sentences']), int(features['uniquewords']), int(features[',']),
                         int(features['.']), int(features['and']), int(features['or']), int(features['a']), int(features['an']),
                         int(features['the']), int(features['in']), int(features['on']), int(features['to']),
                         int(features['of']), int(features['it']), int(features['that']), int(features['as']),
                         int(features['is']), int(features['so'])))
        except:
            print("ERROR: Could not store play feature")
        try:
            conn.commit()
            features['id'] = conn.insert_id()
            return features
        except:
            print("ERROR: Could not store play feature")
            conn.rollback()



collector = featureCollector()
collector.openCon()
# collector.collect_sentences_features(False)
# collector.collect_sentences_features(True)
# collector.collect_scene_features(False)
# collector.collect_scene_features(True)
collector.collect_play_features(False)
collector.collect_play_features(True)
