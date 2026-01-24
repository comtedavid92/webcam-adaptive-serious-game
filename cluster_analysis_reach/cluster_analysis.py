import pandas
import sklearn
import matplotlib.pyplot


# Read the CSV
csv = pandas.read_csv("kinematics.csv")

# Set the features to keep
# The features to keep come from the Excel analysis
features = [
    "wrist_number_of_velocity_peaks",
    "wrist_mean_velocity",
    "wrist_sparc",
    "wrist_jerk",
    "trunk_rom",
    "hand_path_ratio"
]

# Filter the CSV
# Example, data[['col1', 'col2']] keeps only col1 and col2
profiles_frame = csv["profile"]
data_frame = csv[features]

# Get a 2D array (n rows, n columns)
profiles_array = profiles_frame.values
data_array = data_frame.values

# Normalize the data
scaler = sklearn.preprocessing.StandardScaler()
data_array = scaler.fit_transform(data_array)

# Try different number of clusters
# - Inertia is Sum of Squared Errors (SSE)
# - Silouette score tells how well the data points are grouped within their own cluster compared to how separated they are from other clusters
# Source
# - https://www.w3schools.com/python/python_ml_k-means.asp
# - https://www.datacamp.com/tutorial/k-means-clustering-python
# - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
inertia = []
silhouette_score = []
ks = range(2, 10)

for k in ks:
    # Compute K-means
    km = sklearn.cluster.KMeans(n_clusters=k, random_state = 0, n_init='auto')
    labels = km.fit_predict(data_array)
    # Add inertia
    inertia.append(km.inertia_)
    # Add silouhette score
    sc = sklearn.metrics.silhouette_score(data_array, labels)
    silhouette_score.append(sc)

# Diplay the inertia plot
matplotlib.pyplot.figure() # New plot
matplotlib.pyplot.grid(True) # Add grid
matplotlib.pyplot.title("K-means, inertia (SSE)")
matplotlib.pyplot.xlabel("Number of clusters")
matplotlib.pyplot.ylabel("inertia (SSE)")
matplotlib.pyplot.plot(list(ks), inertia, marker="x")
matplotlib.pyplot.show()

# Diplay the silhouette score plot
matplotlib.pyplot.figure() # New plot
matplotlib.pyplot.grid(True) # Add grid
matplotlib.pyplot.title("K-means, silouhette score")
matplotlib.pyplot.xlabel("Number of clusters")
matplotlib.pyplot.ylabel("Silouhette score")
matplotlib.pyplot.plot(list(ks), silhouette_score, marker="x")
matplotlib.pyplot.show()

# Compute validation
# - Here, K-Means is computed with k=4 to assign each data sample to a cluster
# - The obtained cluster labels are then compared with the true profiles using the adjusted rand index to evaluate the clustering result
# Sources
# - https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html
km = sklearn.cluster.KMeans(n_clusters=4, random_state = 0, n_init='auto')
labels = km.fit_predict(data_array)
ari = sklearn.metrics.adjusted_rand_score(profiles_array, labels)
print("ARI:", ari)