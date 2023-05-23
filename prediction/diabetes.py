import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load the data
df = pd.read_csv('diabetes.csv')

# Select the features and the target
X = df[["Pregnancies", "Glucose", "BloodPressure", "BMI", "DiabetesPedigreeFunction", "Age"]]
y = df['Outcome']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define and train the model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Save the trained model to a file
pickle.dump(model, open("diabetes.pkl", 'wb'))

# Load the model from the file
model = pickle.load(open("diabetes.pkl", 'rb'))

# Predict the values for the testing set
y_pred = model.predict(X_test)

# Calculate and print the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy}")

# Get user input for new data
pregnancies = int(input("Enter the number of pregnancies: "))
glucose = int(input("Enter the glucose level: "))
blood_pressure = int(input("Enter the current blood pressure: "))
bmi = float(input("Enter the body mass index: "))
diabetes_pedigree_function = float(input("Enter the diabetes pedigree function: "))
age = int(input("Enter the age: "))

new_data = [[pregnancies, glucose, blood_pressure, bmi, diabetes_pedigree_function, age]]
prediction = model.predict(new_data)

if prediction[0] == 1:
    print("The person is likely to have diabetes.")
else:
    print("The person is likely not to have diabetes.")
