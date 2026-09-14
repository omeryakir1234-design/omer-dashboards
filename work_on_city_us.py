import folium
import pandas as pd
import os
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# 1. טעינת הנתונים מקובץ ה-CSV שיצרנו
df = pd.read_csv("us_cities_data.csv")

# 2. יצירת מפת הבסיס של ארה"ב (מרכז ארה"ב בערך בקואורדינטות [39.8283, -98.5795])
# נשתמש ב-zoom_start=4 כדי לראות את כל ארה"ב
us_map = folium.Map(location = [39.8283, -98.5795], zoom_start = 4)

# פונקציית עזר להגדרת צבע לפי מדד האושר
def get_color(happiness):
    if happiness >= 7.5:
        return "green"
    elif happiness >= 5.5:
        return "orange"
    else:
        return "red"

# 3. הוספת כל עיר למפה כ-CircleMarker (Bubble Plot על גבי מפה)
for idx, row in df.iterrows():
# בניית הטקסט שיופיע בחלון קופץ בלחיצה על העיר
    popup_text = f"""
    <div style="font-family: Arial; width: 180px;">
        <h4><b>{row['city']}, {row['state']}</b></h4>
        <b>Happiness Score:</b> {row['happiness_score']} / 10<br>
        <b>Avg Monthly Salary:</b> ${row['avg_monthly_salary']:,.0f}<br>
        <b>Avg Age:</b> {row['avg_age']}<br>
        <b>Nightlife Spots:</b> {row['nightlife_spots']}<br>
        <b>Cleanliness Score:</b> {row['cleanliness_score']}<br>
        <b>Traffic Index:</b> {row['traffic_index']}
    </div>
    """
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=row["nightlife_spots"] / 10,
        popup=folium.Popup(popup_text, max_width=250),
        tooltip=f"{row['city']} (Happiness: {row['happiness_score']})",
        color=get_color(row["happiness_score"]),
        fill=True,
        fill_color=get_color(row["happiness_score"]),
        fill_opacity=0.6,
    ).add_to(us_map)


# פתיחת המפה בכרום
# us_map.save("us_cities_map.html")
# webbrowser.open("file://" + os.path.realpath("us_cities_map.html"))

##########################################################################################################

# ניתוחים סטטיסטים
# 2. בחירת העמודות הנומריות בלבד לניתוח
numeric_cols = [
    "avg_age",
    "avg_monthly_salary",
    "nightlife_spots",
    "traffic_index",
    "cleanliness_score",
    "happiness_score",
]
df_numeric = df[numeric_cols]

# 3. חישוב מטריצת המתאם (Pearson Correlation)
corr_matrix = df_numeric.corr()

# הדפסת הקורלציות הספציפיות למדד האושר במסוף (Terminal)
print("--- Correlation with Happiness Score ---")
print(corr_matrix["happiness_score"].sort_values(ascending=False))
print("---------------------------------------")

# 4. ויזואליזציה 1: Heatmap של מטריצת הקורלציה
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f")
plt.title("Correlation Matrix of City Features", fontsize=14)
plt.tight_layout()
# plt.show()

# 5. ויזואליזציה 2: Regression Plots - כל מדד מול מדד האושר
features = [
    "avg_monthly_salary",
    "cleanliness_score",
    "nightlife_spots",
    "traffic_index",
    "avg_age",
]

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, col in enumerate(features):
    sns.regplot(
        x=col,
        y="happiness_score",
        data=df_numeric,
        ax=axes[idx],
        color="teal",
        marker="+",
        scatter_kws={"alpha": 0.7},
    )
    # חישוב הערך המדויק של הקורלציה לצורך הוספה למלל
    r_val = corr_matrix.loc[col, "happiness_score"]
    axes[idx].set_title(f"{col} vs Happiness (r = {r_val:.2f})")
    axes[idx].set_ylabel("Happiness Score")

# הסרת התת-גרף ה-6 (המיותר, כי יש לנו 5 תכונות)
fig.delaxes(axes[5])

# plt.tight_layout()
# plt.show()

###################################################################################################
# יצירת ואימון מודלל למציאת קשר בין פרמטרים למדד אושר
# 2. הגדרת משתני הקלט (X) ומשתנה המטרה (y)
X = df[
    [
        "avg_age",
        "avg_monthly_salary",
        "nightlife_spots",
        "traffic_index",
        "cleanliness_score",
    ]
]
y = df["happiness_score"]

# 3. חלוקת הנתונים: 80% לאימון ו-20% לבדיקה
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)

# 4. יצירת המודל ואימונו
model = LinearRegression()
model.fit(X_train, y_train)

# 5. הערכת ביצועי המודל על סט הבדיקה
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)

# print("--- Linear Regression Model Performance ---")
# print(f"R² Score: {r2:.3f}")
# print(f"Mean Squared Error (MSE): {mse:.3f}")
# print("------------------------------------------")

# 6. חיזוי עבור עיר חדשה!
# נניח עיר חדשה עם הפרמטרים הבאים:
# גיל ממוצע: 35, שכר: 7500$, בילויים: 120, פקקים: 4.5, ניקיון: 8.0
new_city_data = pd.DataFrame(
    [
        {
            "avg_age": 35.0,
            "avg_monthly_salary": 7500.0,
            "nightlife_spots": 120,
            "traffic_index": 4.5,
            "cleanliness_score": 8.0,
        }
    ]
)
predicted_happiness = model.predict(new_city_data)
# print(
#     f"\n💡 Predicted Happiness Score for the new city: {predicted_happiness[0]:.2f} / 10"
# )

###############################################################################
# יצירת גרף ברים של ממוצע מדד אושר לפי אזורים
# 2. חישוב מדד האושר הממוצע לכל מדינה (State)
state_happiness = (df.groupby("state")["happiness_score"].mean().reset_index())

# 3. מיוון המדינות לפי מדד האושר מהגבוה לנמוך
state_happiness = state_happiness.sort_values(by = "happiness_score", ascending=False)

# 4. יצירת גרף העמודות
plt.figure(figsize=(12, 6))
barplot = sns.barplot(
    x="state",
    y="happiness_score",
    data=state_happiness,
    palette="viridis",
    hue="state",
    legend=False,
)

# 5. הוספת ערכי הממוצע מעל כל עמודה
for p in barplot.patches:
    barplot.annotate(
        f"{p.get_height():.2f}",
        (p.get_x() + p.get_width() / 2.0, p.get_height()),
        ha="center",
        va="center",
        xytext=(0, 5),
        textcoords="offset points",
        fontsize=9,
    )

# עיצוב הגרף
plt.title("Average Happiness Score by State", fontsize=14, fontweight="bold")
plt.xlabel("State", fontsize=12)
plt.ylabel("Average Happiness Score (1-10)", fontsize=12)
plt.ylim(0, 10)  # הגדרת ציר Y מ-0 עד 10
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()
