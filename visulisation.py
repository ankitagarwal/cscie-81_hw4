from sklearn.decomposition import PCA
import pymysql
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import mixture

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
plt.title("Raw data (scenes) with dimensions reduced to 2 using PCA")
plt.show()

# Let us do K-means now.
km = KMeans(n_clusters=4)
km.fit(X)
labels = km.predict(X)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
label_color = [colors[l] for l in labels]
centroids = km.cluster_centers_
plt.scatter(first, second, c=label_color)
plt.title('K-means clustered data with dimensions reduced to 2 using PCA')
plt.show()

# GMM, here I come.
mix = mixture.GMM(n_components=4, covariance_type='full')
mix.fit(X)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
labels = mix.predict(X)
label_color = [colors[l] for l in labels]
ax = plt.gca()
ax.scatter(first, second, c=label_color, alpha=0.8)
plt.show()
