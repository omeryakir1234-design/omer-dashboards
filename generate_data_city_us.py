import numpy as np
import pandas as pd

# הגדרת Random Seed לשחזור מדויק של התוצאות
np.random.seed(42)

n_samples = 500

# 1. גיל ממוצע בעיר (בין 22 ל-65)
avg_age = np.random.normal(loc=38, scale=6, size=n_samples)
avg_age = np.clip(avg_age, 22, 65)

# 2. שכר חודשי ממוצע בדולרים (קשור מעט לגיל ולשונות מקומית)
avg_monthly_salary = 3000 + (avg_age * 40) + np.random.normal(2000, 800, n_samples)
avg_monthly_salary = np.clip(avg_monthly_salary, 2200, 12000)

# 3. כמות מקומות בילוי (ערים צעירות ועשירות יותר נוטות להכיל יותר בילויים)
nightlife_spots = (
    (60 - avg_age) * 3
    + (avg_monthly_salary / 200)
    + np.random.normal(20, 15, n_samples)
)
nightlife_spots = np.clip(nightlife_spots, 5, 300).astype(int)

# 4. מדד עומס תנועה / פקקים (1-10) - ערים עם הרבה בילויים נוטות להיות עמוסות יותר
traffic_index = (nightlife_spots / 35) + np.random.normal(4, 1.5, n_samples)
traffic_index = np.clip(traffic_index, 1, 10).round(1)

# 5. רמת ניקיון (1-10)
cleanliness_score = (
    (avg_monthly_salary / 1500)
    - (traffic_index * 0.3)
    + np.random.normal(5, 1.2, n_samples)
)
cleanliness_score = np.clip(cleanliness_score, 1, 10).round(1)

# 6. מדד אושר (1-10) - מושפע משכר, ניקיון, בילויים ומוריד מפקקים
happiness_score = (
    3.0
    + (avg_monthly_salary / 2500)
    + (cleanliness_score * 0.35)
    + (nightlife_spots / 80)
    - (traffic_index * 0.25)
    + np.random.normal(0, 0.6, n_samples)
)
happiness_score = np.clip(happiness_score, 1, 10).round(1)

# יצירת ה-DataFrame
df = pd.DataFrame(
    {
        "avg_age": avg_age.round(1),
        "avg_monthly_salary": avg_monthly_salary.round(2),
        "nightlife_spots": nightlife_spots,
        "traffic_index": traffic_index,
        "cleanliness_score": cleanliness_score,
        "happiness_score": happiness_score,
    }
)

# שמירה לקובץ CSV
df.to_csv("us_cities_data.csv", index=False)
print("הקובץ us_cities_data.csv נוצר בהצלחה עם 500 רשומות!")