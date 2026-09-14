import numpy as np
import pandas as pd

np.random.seed(42)
n = 100

# 1. יצירת דפוסי התנהגות מוגדרים (3 פרופילים של לקוחות)
# פרופיל 0: צופים כבדים, מעט פניות לתמיכה, מנויים יציבים (לא נוטשים)
# פרופיל 1: צופים מעט, המון פניות לתמיכה, מחיר גבוה (בסיכון נטישה גבוה)
# פרופיל 2: משתמשים ממוצעים/חדשים

profiles = np.random.choice([0, 1, 2], size=n, p=[0.4, 0.35, 0.25])

hours_watched = []
support_calls = []
monthly_charges = []
tenure_months = []

for p in profiles:
    if p == 0:  # "היציבים"
        hours_watched.append(np.random.uniform(20, 38))
        support_calls.append(np.random.randint(0, 3))
        monthly_charges.append(
            np.random.choice([9.99, 14.99])
        )  # זול-בינוני
        tenure_months.append(np.random.randint(12, 48))
    elif p == 1:  # "בסיכון נטישה"
        hours_watched.append(np.random.uniform(1, 10))
        support_calls.append(np.random.randint(4, 9))
        monthly_charges.append(
            np.random.choice([14.99, 19.99])
        )  # בינוני-יקר
        tenure_months.append(np.random.randint(1, 12))
    else:  # "ממוצעים"
        hours_watched.append(np.random.uniform(10, 22))
        support_calls.append(np.random.randint(1, 5))
        monthly_charges.append(np.random.choice([9.99, 14.99, 19.99]))
        tenure_months.append(np.random.randint(6, 30))

hours_watched = np.round(hours_watched, 1)

# 2. הגדרת משתנה הנטישה (Churn) המבוסס ישר על החוקיות
# אם הלקוח מפרופיל 1 -> בסבירות גבוהה מאוד נוטש (1)
churn = []
for i in range(n):
    if profiles[i] == 1:
        churn.append(1 if np.random.rand() < 0.85 else 0)
    elif profiles[i] == 0:
        churn.append(0 if np.random.rand() < 0.95 else 1)
    else:
        churn.append(1 if np.random.rand() < 0.3 else 0)

# בניית ה-DataFrame
df = pd.DataFrame(
    {
        "user_id": [f"USER_{1000 + i}" for i in range(n)],
        "age": np.random.randint(18, 65, size=n),
        "tenure_months": tenure_months,
        "monthly_charges": monthly_charges,
        "weekly_hours_watched": hours_watched,
        "support_calls": support_calls,
        "churn": churn,
    }
)

# שמירה לקובץ
df.to_csv("streaming_churn_structured.csv", index=False)
print("הקובץ streaming_churn_structured.csv נוצר בהצלחה!")
