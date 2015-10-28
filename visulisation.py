from sklearn.decomposition import PCA
import pymysql
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import mixture
from scipy.spatial.distance import cdist

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
X = X.as_matrix()
pca = PCA(2)
pca.fit(X)
X_proj = pca.transform(X)
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
plt.title('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
          'outliers are marked with x')

# Let us find 5 points which are furthest from their centroid.
outliers = np.array([[0, 0],
                     [0, 0],
                     [0, 0],
                     [0, 0],
                     [0, 0]])
centroids = km.cluster_centers_
for index, point in enumerate(X):
    dist = np.linalg.norm(point - centroids[labels[index]])
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
    plt.scatter(first[outlier[0]], second[outlier[0]], c='blue', marker='x', s=50)

plt.show()
print(outliers)

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
plt.title('K-means clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
          'outliers are marked with x')

# Let us find 5 points which are furthest from their centroid.
outliers = np.array([[0, 0],
                     [0, 0],
                     [0, 0],
                     [0, 0],
                     [0, 0]])
centroids = km.cluster_centers_
for index, point in enumerate(X):
    dist = np.linalg.norm(point - centroids[labels[index]])
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
    plt.scatter(first[outlier[0]], second[outlier[0]], c='blue', marker='x', s=50)
plt.show()
print(outliers)

# GMM, here I come for data without punctuation.
miX_cleaned = mixture.GMM(n_components=4, covariance_type='full')
miX_cleaned.fit(X_cleaned)
colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
labels = miX_cleaned.predict(X_cleaned)
label_color = [colors[l] for l in labels]
aX_cleaned = plt.gca()
aX_cleaned.scatter(first, second, c=label_color, alpha=0.8)
plt.title('GMM clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)')
plt.show()
