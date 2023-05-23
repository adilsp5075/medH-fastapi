import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load the data
DATA_PATH = "cancer.csv"
df = pd.read_csv(DATA_PATH)

# Preprocess the data
le = LabelEncoder()
df['diagnosis'] = le.fit_transform(df['diagnosis'])  # Convert diagnosis M/B to 1/0

# Select the features and the target
X = df[["radius_mean", "area_mean", "perimeter_mean", "concavity_mean", "concave points_mean"]]
y = df['diagnosis']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define and train the model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Save the trained model to a file
pickle.dump(model, open("cancer.pkl", 'wb'))

# Load the model from the file
model = pickle.load(open("cancer.pkl", 'rb'))

# Predict the values for the testing set
y_pred = model.predict(X_test)

# Calculate and print the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy}")

# Get user input for new data
radius_mean = float(input("Enter the Mean of the Radius: "))
area_mean = float(input("Enter the Mean of the Area: "))
perimeter_mean = float(input("Enter the Mean of the Perimeter: "))
concavity_mean = float(input("Enter the Mean of the Concavity: "))
concave_points_mean = float(input("Enter the Mean of the Concave Points: "))

new_data = [[radius_mean, area_mean, perimeter_mean, concavity_mean, concave_points_mean]]  # Example data
prediction = model.predict(new_data)

if prediction[0] == 1:
    print("The cancer is malignant.")
else:
    print("The cancer is benign.")
