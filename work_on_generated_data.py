import numpy as np
import pandas as pd

# רשימת ערים מרכזיות בארה"ב עם קואורדינטות מדויקות (Latitude, Longitude)
cities_data = [
    {"city": "New York", "state": "NY", "lat": 40.7128, "lon": -74.0060},
    {"city": "Los Angeles", "state": "CA", "lat": 34.0522, "lon": -118.2437},
    {"city": "Chicago", "state": "IL", "lat": 41.8781, "lon": -87.6298},
    {"city": "Houston", "state": "TX", "lat": 29.7604, "lon": -95.3698},
    {"city": "Phoenix", "state": "AZ", "lat": 33.4484, "lon": -112.0740},
    {"city": "Philadelphia", "state": "PA", "lat": 39.9526, "lon": -75.1652},
    {"city": "San Antonio", "state": "TX", "lat": 29.4241, "lon": -98.4936},
    {"city": "San Diego", "state": "CA", "lat": 32.7157, "lon": -117.1611},
    {"city": "Dallas", "state": "TX", "lat": 32.7767, "lon": -96.7970},
    {"city": "San Jose", "state": "CA", "lat": 37.3382, "lon": -121.8863},
    {"city": "Austin", "state": "TX", "lat": 30.2672, "lon": -97.7431},
    {"city": "Jacksonville", "state": "FL", "lat": 30.3322, "lon": -81.6557},
    {"city": "Fort Worth", "state": "TX", "lat": 32.7555, "lon": -97.3308},
    {"city": "Columbus", "state": "OH", "lat": 39.9612, "lon": -82.9988},
    {"city": "Indianapolis", "state": "IN", "lat": 39.7684, "lon": -86.1581},
    {"city": "Charlotte", "state": "NC", "lat": 35.2271, "lon": -80.8431},
    {"city": "San Francisco", "state": "CA", "lat": 37.7749, "lon": -122.4194},
    {"city": "Seattle", "state": "WA", "lat": 47.6062, "lon": -122.3321},
    {"city": "Denver", "state": "CO", "lat": 39.7392, "lon": -104.9903},
    {"city": "Washington", "state": "DC", "lat": 38.9072, "lon": -77.0369},
    {"city": "Nashville", "state": "TN", "lat": 36.1627, "lon": -86.7816},
    {"city": "Oklahoma City", "state": "OK", "lat": 35.4676, "lon": -97.5164},
    {"city": "El Paso", "state": "TX", "lat": 31.7619, "lon": -106.4850},
    {"city": "Boston", "state": "MA", "lat": 42.3601, "lon": -71.0589},
    {"city": "Portland", "state": "OR", "lat": 45.5152, "lon": -122.6784},
    {"city": "Las Vegas", "state": "NV", "lat": 36.1699, "lon": -115.1398},
    {"city": "Memphis", "state": "TN", "lat": 35.1495, "lon": -90.0490},
    {"city": "Detroit", "state": "MI", "lat": 42.3314, "lon": -83.0458},
    {"city": "Baltimore", "state": "MD", "lat": 39.2904, "lon": -76.6122},
    {"city": "Milwaukee", "state": "WI", "lat": 43.0389, "lon": -87.9065},
    {"city": "Albuquerque", "state": "NM", "lat": 35.0844, "lon": -106.6504},
    {"city": "Tucson", "state": "AZ", "lat": 32.2226, "lon": -110.9747},
    {"city": "Fresno", "state": "CA", "lat": 36.7468, "lon": -119.7726},
    {"city": "Sacramento", "state": "CA", "lat": 38.5816, "lon": -121.4944},
    {"city": "Mesa", "state": "AZ", "lat": 33.4152, "lon": -111.8315},
    {"city": "Atlanta", "state": "GA", "lat": 33.7490, "lon": -84.3880},
    {"city": "Kansas City", "state": "MO", "lat": 39.0997, "lon": -94.5786},
    {"city": "Colorado Springs", "state": "CO", "lat": 38.8339, "lon": -104.8214},
    {"city": "Miami", "state": "FL", "lat": 25.7617, "lon": -80.1918},
    {"city": "Raleigh", "state": "NC", "lat": 35.7796, "lon": -78.6382},
    {"city": "Omaha", "state": "NE", "lat": 41.2565, "lon": -95.9345},
    {"city": "Long Beach", "state": "CA", "lat": 33.7701, "lon": -118.1937},
    {"city": "Virginia Beach", "state": "VA", "lat": 36.8529, "lon": -75.9780},
    {"city": "Oakland", "state": "CA", "lat": 37.8044, "lon": -122.2712},
    {"city": "Minneapolis", "state": "MN", "lat": 44.9778, "lon": -93.2650},
    {"city": "Tulsa", "state": "OK", "lat": 36.1539, "lon": -95.9928},
    {"city": "Tampa", "state": "FL", "lat": 27.9506, "lon": -82.4572},
    {"city": "Arlington", "state": "TX", "lat": 32.7357, "lon": -97.1081},
    {"city": "New Orleans", "state": "LA", "lat": 29.9511, "lon": -90.0715},
    {"city": "Wichita", "state": "KS", "lat": 37.6872, "lon": -97.3301},
]

df = pd.DataFrame(cities_data)
np.random.seed(42)
n_samples = len(df)

# יצירת המשתנים הסטטיסטיים עבור כל עיר
df["avg_age"] = np.clip(
    np.random.normal(loc=37, scale=5, size=n_samples), 24, 60
).round(1)

# שכר חודשי
df["avg_monthly_salary"] = (
    4000 + (df["avg_age"] * 30) + np.random.normal(2000, 900, n_samples)
).round(2)
df["avg_monthly_salary"] = np.clip(df["avg_monthly_salary"], 2800, 11000)

# מקומות בילוי
df["nightlife_spots"] = (
    (60 - df["avg_age"]) * 2.5
    + (df["avg_monthly_salary"] / 180)
    + np.random.normal(10, 15, n_samples)
).astype(int)
df["nightlife_spots"] = np.clip(df["nightlife_spots"], 10, 250)

# עומס תנועה (1-10)
df["traffic_index"] = (
    (df["nightlife_spots"] / 30) + np.random.normal(4, 1.2, n_samples)
).round(1)
df["traffic_index"] = np.clip(df["traffic_index"], 1.0, 10.0)

# רמת ניקיון (1-10)
df["cleanliness_score"] = (
    (df["avg_monthly_salary"] / 1400)
    - (df["traffic_index"] * 0.3)
    + np.random.normal(5, 1.0, n_samples)
).round(1)
df["cleanliness_score"] = np.clip(df["cleanliness_score"], 1.0, 10.0)

# מדד אושר (1-10)
df["happiness_score"] = (
    3.0
    + (df["avg_monthly_salary"] / 2200)
    + (df["cleanliness_score"] * 0.35)
    + (df["nightlife_spots"] / 90)
    - (df["traffic_index"] * 0.3)
    + np.random.normal(0, 0.5, n_samples)
).round(1)
df["happiness_score"] = np.clip(df["happiness_score"], 1.0, 10.0)

# שמירה לקובץ CSV
df.to_csv("us_cities_data.csv", index=False)
print("הקובץ us_cities_data.csv נוצר בהצלחה עם 50 ערים בארה\"ב וקואורדינטות!")
