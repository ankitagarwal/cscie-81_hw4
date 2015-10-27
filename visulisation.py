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

# Raw data plot
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
plt.title("Raw data (scenes with punctuations) with dimensions reduced to 2 using PCA")
plt.show()

# Cleaned Raw data plot
cur.execute("Select * from features_scenes_cleaned")
X_cleaned = []
for row in cur:
    X_cleaned.append(row)
X_cleaned = pd.DataFrame(X_cleaned)
X_cleaned.drop('id', 1)
X_cleaned.drop('sceneId', 1)
pca = PCA(2)
pca.fit(X_cleaned)
X_cleaned_proj = pca.transform(X_cleaned)
print(X_cleaned_proj)
first = X_cleaned_proj.T[0].T
second = X_cleaned_proj.T[1].T
plt.scatter(first, second, marker='o')
plt.title("Raw data (scenes  without punctuations) with dimensions reduced to 2 using PCA")
plt.show()

# Let us do K-means now.
km = KMeans(n_clusters=4)
km.fit(X)
labels = km.predict(X)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
label_color = [colors[l] for l in labels]
plt.scatter(first, second, c=label_color)
plt.title('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)')
plt.show()

# GMM, here I come.
mix = mixture.GMM(n_components=4, covariance_type='full')
mix.fit(X)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
labels = mix.predict(X)
label_color = [colors[l] for l in labels]
ax = plt.gca()
ax.scatter(first, second, c=label_color, alpha=0.8)
plt.title('GMM clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)')
plt.show()

# Let us do K-means now for data without punctuation.
km = KMeans(n_clusters=4)
km.fit(X_cleaned)
labels = km.predict(X_cleaned)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
label_color = [colors[l] for l in labels]
plt.scatter(first, second, c=label_color)
plt.title('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)')
plt.show()

# GMM, here I come for data without punctuation.
miX_cleaned = mixture.GMM(n_components=4, covariance_type='full')
miX_cleaned.fit(X_cleaned)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
labels = miX_cleaned.predict(X_cleaned)
label_color = [colors[l] for l in labels]
aX_cleaned = plt.gca()
aX_cleaned.scatter(first, second, c=label_color, alpha=0.8)
plt.title('GMM clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)')
plt.show()
