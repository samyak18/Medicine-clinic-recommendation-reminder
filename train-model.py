import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

# Load dataset (use correct separator based on your file)
file_path = "C:\\Users\\kumar\\Downloads\\archive (2)\\drugsComTrain_raw.csv"

df = pd.read_csv("C:\\Users\\kumar\\Downloads\\archive (2)\\drugsComTrain_raw.csv")

# Clean column names
df.columns = df.columns.str.strip().str.lower()
print("Columns:", df.columns)

# Select correct drug column
if 'drugname' in df.columns:
    drug_col = 'drugname'
elif 'drug' in df.columns:
    drug_col = 'drug'
else:
    raise ValueError("Drug column not found")

# Select required columns
df = df[['condition', drug_col, 'rating']].dropna()

# Rename for consistency
df.rename(columns={drug_col: 'drugname'}, inplace=True)

# Filter good drugs
df = df[df['rating'] > 6]

# Remove duplicates
df = df.drop_duplicates()

# Features and target
X = df['condition']
y = df['drugname']

# Convert text → vectors
vectorizer = TfidfVectorizer(stop_words='english')
X_vectorized = vectorizer.fit_transform(X)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_vectorized, y)

# Save model
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model trained successfully!")