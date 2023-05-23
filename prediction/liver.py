import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

# Load the data
df = pd.read_csv('indian_liver_patient.csv')

# Preprocess the data
df['Gender'] = df['Gender'].apply(lambda x: 1 if x == 'Male' else 0)

# Fill NaN values with the mean of the column
df = df.fillna(df.mean())

# Select the features and the target
X = df[["Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase", 
        "Alamine_Aminotransferase", "Total_Protiens", "Albumin", 
        "Albumin_and_Globulin_Ratio"]]
y = df['Dataset']

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
with open('liver.pkl', 'wb') as file:
    pickle.dump(model, file)

# Let's predict with user input
Total_Bilirubin = float(input("Enter Total Bilirubin: "))
Direct_Bilirubin = float(input("Enter Direct Bilirubin: "))
Alkaline_Phosphotase = int(input("Enter Alkaline Phosphotase: "))
Alamine_Aminotransferase = int(input("Enter Alamine Aminotransferase: "))
Total_Protiens = float(input("Enter Total Proteins: "))
Albumin = float(input("Enter Albumin: "))
Albumin_and_Globulin_Ratio = float(input("Enter Albumin and Globulin Ratio: "))

new_data = [[Total_Bilirubin, Direct_Bilirubin, Alkaline_Phosphotase,
             Alamine_Aminotransferase, Total_Protiens, Albumin, 
             Albumin_and_Globulin_Ratio]]

prediction = model.predict(new_data)

if prediction[0] == 1:
    print("The patient is likely to have a liver disease.")
else:
    print("The patient is likely not to have a liver disease.")
