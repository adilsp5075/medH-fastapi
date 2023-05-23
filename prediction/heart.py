import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

# Load the data
df = pd.read_csv('heart.csv')

# Select the features and the target
X = df[["cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang"]]
y = df['target']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define and train the model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Predict the values for the testing set
y_pred = model.predict(X_test)

# Calculate and print the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy}")

# Save the model
with open('heart.pkl', 'wb') as file:
    pickle.dump(model, file)

# Let's predict with user input
cp = int(input("Enter the Chest Pain Type (0-3): "))
trestbps = int(input("Enter the Resting Blood Pressure (in mm Hg): "))
chol = int(input("Enter the Serum Cholestoral in mg/dl: "))
fbs = int(input("Enter the Fasting Blood Sugar (> 120 mg/dl, 1 = true; 0 = false): "))
restecg = int(input("Enter the Resting Electrocardiographic Results (0-2): "))
thalach = int(input("Enter the Maximum Heart Rate Achieved: "))
exang = int(input("Enter the Exercise Induced Angina (1 = yes; 0 = no): "))

new_data = [[cp, trestbps, chol, fbs, restecg, thalach, exang]]

prediction = model.predict(new_data)

if prediction[0] == 1:
    print("The person is likely to have heart disease.")
else:
    print("The person is likely not to have heart disease.")
