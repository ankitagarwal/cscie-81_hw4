from sklearn.decomposition import PCA
import pymysql
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#########
# Open a MySQL connection. Should be triggered by the caller before running
# the scraper, if the caller is using MySQL
#########
def openCon():
    global conn
    global cur
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='mysql', charset='utf8')

    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("USE shakespeare")

openCon()
cur.execute("Select * from features_scenes")
X = []
for row in cur:
    X.append(row)
X = pd.DataFrame(X)
X.drop('id', 1)
X.drop('sceneId', 1)
pca = PCA(2)
pca.fit(X)
X_proj = pca.transform(X)
print(X_proj)
first = X_proj.T[0].T
second = X_proj.T[1].T
plt.scatter(first, second, marker='o')
plt.show()