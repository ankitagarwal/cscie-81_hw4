#load the iris data set
from sklearn import datasets
from sklearn import cross_validation
from sklearn.tree import DecisionTreeClassifier
from sklearn.cross_validation import cross_val_score
from sklearn import tree
from sklearn.externals.six import StringIO
import matplotlib.pyplot as plt
 
import pydot 

iris = datasets.load_iris()

X = iris.data  
Y = iris.target

print(X.shape, Y.shape)
# put test data aside

X_train, X_test, Y_train, Y_test = cross_validation.train_test_split(X, Y, test_size=0.33, random_state=42)


clf = DecisionTreeClassifier().fit(X_train, Y_train)
print(clf)
with open("iris.dot", 'w') as f:
	tree.export_graphviz(clf, out_file=f)
	graph = pydot.graph_from_dot_data(f.getvalue()) 
	graph.write_pdf("iris.pdf") 

