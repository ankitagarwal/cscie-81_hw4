from sklearn.decomposition import PCA
import pymysql
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import mixture
from sklearn.preprocessing import StandardScaler

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


def do_kmeans(title, X, first, second, clusters = 4):
    # Let us do K-means now.
    km = KMeans(n_clusters=clusters)
    km.fit(X)
    labels = km.predict(X)
    colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
    label_color = [colors[l] for l in labels]
    plt.scatter(first, second, c=label_color)
    plt.title(title)

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
    print(title)
    print("Detected outliers are - (index, distance from centroid) -")
    print(outliers)


def do_gmm(title, X, first, second, clusters = 4):
    # GMM, here I come.
    mix = mixture.GMM(n_components=clusters, covariance_type='full')
    mix.fit(X)
    colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']
    labels = mix.predict(X)
    label_color = [colors[l] for l in labels]
    ax = plt.gca()
    ax.scatter(first, second, c=label_color, alpha=0.8)
    plt.title(title)
    plt.show()


def prep_data(cur):
    X = []
    for row in cur:
        X.append(row)
    X = pd.DataFrame(X)
    X.drop('id', 1)
    X.drop('sceneId', 1)
    X = X.as_matrix()
    X = StandardScaler().fit_transform(X)
    pca = PCA(2)
    pca.fit(X)
    X_proj = pca.transform(X)
    first = X_proj.T[0].T
    second = X_proj.T[1].T
    return [X, first, second]


openCon()
# Raw data plot
cur.execute("Select * from features_scenes")
X, first, second = prep_data(cur)
plt.scatter(first, second, marker='o')
plt.title("Raw data (scenes with punctuations) with dimensions reduced to 2 using PCA")
plt.show()

# Cleaned Raw data plot
cur.execute("Select * from features_scenes_cleaned")
X_cleaned, first_cleaned, second_cleaned = prep_data(cur)
plt.scatter(first_cleaned, second_cleaned, marker='o')
plt.title("Raw data (scenes  without punctuations) with dimensions reduced to 2 using PCA")
plt.show()

# K-means for data with punctuation.
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
              'outliers are marked with x (3 Clusters)', X, first, second, 3)
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
              'outliers are marked with x (4 Clusters)', X, first, second, 4)
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
              'outliers are marked with x (5 Clusters)', X, first, second, 5)


# GMM for data with punctuation.
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
       '(3 clusters)', X, first, second, 3)
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
       '(3 clusters)', X, first, second, 4)
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  with punctuations)\n'
       '(3 clusters)', X, first, second, 5)


# Let us do K-means now for data without punctuation.
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
              'outliers are marked with x (3 Clusters)', X_cleaned, first_cleaned, second_cleaned, 3)
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
              'outliers are marked with x (4 Clusters)', X_cleaned, first_cleaned, second_cleaned, 4)
do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
              'outliers are marked with x (5 Clusters)', X_cleaned, first_cleaned, second_cleaned, 5)

# GMM, here I come for data without punctuation.
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
       '(3 clusters)', X_cleaned, first, second, 3)
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
       '(3 clusters)', X_cleaned, first, second, 4)
do_gmm('GMM clustered data with dimensions reduced to 2 using PCA (scenes  without punctuations)\n'
       '(3 clusters)', X_cleaned, first, second, 5)
