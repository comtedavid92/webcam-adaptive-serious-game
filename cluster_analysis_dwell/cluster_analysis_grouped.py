import pandas
import sklearn
import matplotlib.pyplot

# Get the CSV as a data frame
# https://pandas.pydata.org/docs/getting_started/intro_tutorials/02_read_write.html
csv = pandas.read_csv("kinematics_grouped.csv")

# Get two subsets of the data frame
# https://pandas.pydata.org/docs/getting_started/intro_tutorials/03_subset_data.html
profiles_frame = csv["profile"]
data_frame = csv[[
    "wrist_mean_velocity"
]]

# Normalize the data
# https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.scale.html
data_frame = sklearn.preprocessing.scale(data_frame)

# Set the comparison metrics
# https://medium.com/@jeffzyme/understanding-inertia-distortion-and-silhouette-scores-and-their-differences-key-metrics-for-458fe28ce2aa
inertias = []
silhouette_scores = []

# Compute k-means with different numbers of clusters
# https://www.w3schools.com/python/python_ml_k-means.asp
ks = range(2, 10)
for k in ks:
    kmeans = sklearn.cluster.KMeans(n_clusters=k, random_state=0) # The parameter random_state=0 is used for reproducibility
    labels = kmeans.fit_predict(data_frame) # The labels variable contains the assigned cluster index for each data
    inertias.append(kmeans.inertia_) # The inertia is the sum of the squared distances of each data point to its cluster centroid
    score = sklearn.metrics.silhouette_score(data_frame, labels) # The silhouette score indicates how well the data belong to their cluster and how far they are from other clusters
    silhouette_scores.append(score)

# Diplay the inertias plot
matplotlib.pyplot.figure() # New plot
matplotlib.pyplot.grid(True) # Add grid
matplotlib.pyplot.title("K-means | dwell step | inertia")
matplotlib.pyplot.xlabel("Number of clusters")
matplotlib.pyplot.ylabel("Inertia")
matplotlib.pyplot.plot(list(ks), inertias, marker="x")
matplotlib.pyplot.show()

# Diplay the silhouette score plot
matplotlib.pyplot.figure() # New plot
matplotlib.pyplot.grid(True) # Add grid
matplotlib.pyplot.title("K-means | dwell step | silhouette score")
matplotlib.pyplot.xlabel("Number of clusters")
matplotlib.pyplot.ylabel("Silhouette score")
matplotlib.pyplot.plot(list(ks), silhouette_scores, marker="x")
matplotlib.pyplot.show()

# Compute the adjusted rand index
# https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html
k = 2
kmeans = sklearn.cluster.KMeans(n_clusters=k, random_state = 0)
labels = kmeans.fit_predict(data_frame)
ari = sklearn.metrics.adjusted_rand_score(profiles_frame, labels)
print("Adjusted rand index : " + str(ari))