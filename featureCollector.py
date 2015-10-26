import nltk
import pymysql
import collections
from nltk.tokenize import RegexpTokenizer

from play import Play
from character import Character
from scene import Scene
from line import Line

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
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='mysql', charset='utf8')

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

    def get_words(self):
        global conn
        global cur
        cur.execute("Select * from words")
        return cur

    def get_scenes(self):
        global conn
        global cur
        cur.execute("SET SESSION group_concat_max_len = 100000;")
        cur.execute("Select scenes.id, COUNT(Distinct characterId) AS characterCount, GROUP_CONCAT(lineText SEPARATOR ' ') AS fullSceneText from words JOIN scenes ON words.sceneId = scenes.id GROUP BY scenes.id")
        return cur

    def collect_words_features(self):
        words = self.get_words()
        all_features = []
        for row in words:
            features = {}
            lineObj = Line(row['id'], row['sceneId'], row['characterId'], row['lineText'])
            tokenizer = RegexpTokenizer(r'\w+')
            tokens = tokenizer.tokenize(lineObj.lineText)
            wordcounts = collections.Counter(tokens)
            features['uniquewords'] = len(wordcounts)
            features['words'] = len(tokens)
            features['chars'] = len(lineObj.lineText)
            features['lineid'] = lineObj.id
            for element in self.get_feature_list():
                features[element] = wordcounts[element]
            all_features.append(features)
        for features in all_features:
            features = self.storeLineFeature(features)
        return 1

    #Stores line features to database
    #Note: There are tons of reserved words here, hence _count is added.
    def storeLineFeature(self, features):
        global conn
        global cur
        try:
            cur.execute("INSERT INTO features_words "
                        "(lineId, chars_count, words_count, uniquewords_count, comma_count, dot_count, and_count,"
                        "or_count, a_count, an_count, the_count, in_count, on_count, to_count, of_count, it_count,"
                        "that_count, as_count, is_count, so_count) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (int(features['lineid']), int(features['chars']), int(features['words']), int(features['uniquewords']), int(features[',']),
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

    def collect_scene_features(self):
        scenes = self.get_scenes()
        all_features = []
        for row in scenes:
            features = {}
            tokenizer = RegexpTokenizer(r'\w+')
            tokens = tokenizer.tokenize(row['fullSceneText'])
            wordcounts = collections.Counter(tokens)
            features['characters'] = row['characterCount']
            features['uniquewords'] = len(wordcounts)
            features['words'] = len(tokens)
            features['chars'] = len(row['fullSceneText'])
            features['sceneid'] = row['id']
            for element in self.get_feature_list():
                features[element] = wordcounts[element]
            all_features.append(features)
        for features in all_features:
            features = self.storeSceneFeature(features)
        return 1

    #Stores scene features to database
    #Note: There are tons of reserved words here, hence _count is added.
    def storeSceneFeature(self, features):
        global conn
        global cur
        try:
            cur.execute("INSERT INTO features_scenes "
                        "(sceneId, character_count, chars_count, words_count, uniquewords_count, comma_count, dot_count, and_count,"
                        "or_count, a_count, an_count, the_count, in_count, on_count, to_count, of_count, it_count,"
                        "that_count, as_count, is_count, so_count) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (int(features['sceneid']), int(features['characters']), int(features['chars']), int(features['words']), int(features['uniquewords']), int(features[',']),
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

collector = featureCollector()
collector.openCon()
words = collector.collect_scene_features()
