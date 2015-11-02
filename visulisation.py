from sklearn.decomposition import PCA
import pymysql
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import mixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

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


# Perform K-means clustering.
def do_kmeans(title, X, first, second, clusters = 4, timeline = False):
    # Let us do K-means now.
    km = KMeans(n_clusters=clusters)
    km.fit(X)
    labels = km.predict(X)
    colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    label_color = [colors[l] for l in labels]
    plt.scatter(first, second, marker='o', c=label_color)
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
    silhouetteAvg = silhouette_score(X, labels)

    plt.show()
    print(title)
    print("Detected outliers are - (index, distance from centroid) -")
    print(outliers)
    print("Silhouette score - ", silhouetteAvg)
    clusters = km.labels_.tolist()
    if timeline:
        clusterTimeline(X, clusters, title)

# Perform GMM clustering.
def do_gmm(title, X, first, second, clusters = 4):
    # GMM, here I come.
    mix = mixture.GMM(n_components=clusters, covariance_type='full')
    mix.fit(X)
    colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    labels = mix.predict(X)
    label_color = [colors[l] for l in labels]
    silhouetteAvg = silhouette_score(X, labels)
    ax = plt.gca()
    ax.scatter(first, second, c=label_color, alpha=0.8)
    plt.title(title)
    # plt.show()
    print("Silhouette score - ", silhouetteAvg)

# Clean data and get it ready for clustering.
def prep_data(cur):
    X = []
    for row in cur:
        X.append(row)
    X = pd.DataFrame(X)
    X.drop('id', 1)
    if 'sceneID' in X:
        X.drop('sceneId', 1)
    if 'playID' in X:
        X.drop('playId', 1)
    X = X.as_matrix()
    X = StandardScaler().fit_transform(X)
    pca = PCA(2)
    pca.fit(X)
    X_proj = pca.transform(X)
    first = X_proj.T[0].T
    second = X_proj.T[1].T
    return [X, first, second]


def clusterTimeline(X, clusters, figureTitle):
    global conn
    global cur

    #bigrams must exist in 30% of the plays
    titles = []
    genres = []
    genrePos = {'COMEDY': 1, 'TRAGEDY': 2, 'HISTORY': 3, 'POETRY': 4}
    years = []
    texts = []
    cur.execute("SELECT * FROM `plays`")
    for row in cur:
        titles.append(row['title'])
        years.append(row['year'])
        genres.append(genrePos[row['type']])

    #If plays are in the same year and genre (this happens
    #in a couple cases, this will offset them a little to make
    #The distinction in the final chart clear)
    for i in range(len(years)):
        for j in range(i+1, len(years)):
            if years[i] == years[j] and genres[i] == genres[j]:
                genres[j] = genres[j] + .25
                years[j] = years[j] + .25



    cluster_colors = {0: '#1f77b4', 1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5:'#8c564b', 6: '#e377c2', 7:'#7f7f7f', 8:'#bcbd22', 9:'#17becf'}

    clusterDict = dict()
    for j in range(len(clusters)):
        clustId = clusters[j]
        #Iterate through the clusters and group scenes names
        if clustId not in clusterDict:
            clusterDict[clustId] = ""
        clusterDict[clustId] += titles[j]+", "
    for k, v in clusterDict.items():
        print(str(k)+": "+str(v))

        print(len(years))
        print(len(genres))
        print(len(clusters))
        print(len(titles))

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
        plt.suptitle(figureTitle, fontsize=20)
        plt.show()


openCon()
# # Raw data plot
# cur.execute("Select * from features_scenes")
# X, first, second = prep_data(cur)
# plt.scatter(first, second, marker='o')
# plt.title("Raw data (scenes with punctuations) with dimensions reduced to 2 using PCA")
# plt.show()
#
# # Cleaned Raw data plot
# cur.execute("Select * from features_scenes_cleaned")
# X_cleaned, first_cleaned, second_cleaned = prep_data(cur)
# plt.scatter(first_cleaned, second_cleaned, marker='o')
# plt.title("Raw data (scenes  without punctuations) with dimensions reduced to 2 using PCA")
# plt.show()
#
# # K-means for data with punctuation.
# for i in range(2, 10):
#     do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA \n(scenes  with punctuations)\n'
#               'outliers are marked with x (' + str(i) +' Clusters)', X, first, second, i)
#
#
# # GMM for data with punctuation.
# for i in range(2, 10):
#     do_gmm('GMM clustered data with dimensions reduced to 2 using PCA \n(scenes  with punctuations)\n'
#            '(' + str(i) +' clusters)', X, first, second, i)
#
#
# # Let us do K-means now for data without punctuation.
# for i in range(2, 10):
#     do_kmeans('K-means clustered data with dimensions reduced to 2 using PCA \n(scenes  without punctuations)\n'
#                   'outliers are marked with x (' + str(i) +' Clusters)', X_cleaned, first_cleaned, second_cleaned, i)
#
# # GMM, here I come for data without punctuation.
# for i in range(2, 10):
#     do_gmm('GMM clustered data with dimensions reduced to 2 using PCA \n(scenes  without punctuations)\n'
#            '(' + str(i) +' clusters)', X_cleaned, first, second, i)


# Play clustering
cur.execute("Select * from features_plays")
X, first, second = prep_data(cur)
plt.scatter(first, second, marker='o')
plt.title("Raw data (scenes with punctuations) with dimensions reduced to 2 using PCA")
plt.show()

# K-means for data with punctuation.
for i in range(2, 10):
    do_kmeans('K-means clustered play data (with punctuations)\n'
              'outliers are marked with x (' + str(i) +' Clusters)', X, first, second, i, True)