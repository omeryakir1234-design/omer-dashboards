import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import random 

df = pd.read_csv('people_data_english.csv')

#גרף עמודות של ממוצע גובה לפי מדינות
# mean_height = df.groupby('Country')['Height_cm'].mean()
# plt.figure(figsize=(8,5))
# bars = plt.bar(mean_height.index, mean_height.values, color = 'skyblue', edgecolor = 'black')
# plt.bar_label(bars, padding = 3)
# plt.title('average hieght by country')
# plt.xlabel('country')
# plt.ylabel('average hieght in cm')
# plt.xticks(rotation = 0)
# plt.show()

#ערך קורולציה
# correlation = df['Height_cm'].corr(df['Weight_kg'])
# print(correlation)

#קו מגמה בין משקל לגובה
# x = df['Height_cm']
# y = df['Weight_kg']
# m, b = np.polyfit(x, y, 1)
# plt.plot(x, m * x + b, color = 'red', linestyle = '--', label = 'Trendline')
# plt.scatter(x, y, color = 'teal', alpha= 0.9, edgecolors = 'black', s = 60, label = 'Data Points')
# plt.title('Relationship Between Height and Weight')
# plt.xlabel('Height (cm)')
# plt.ylabel('Weight (kg)')
# plt.grid(True, linestyle = '--', alpha = 0.5)
# plt.legend()
# plt.tight_layout()
# plt.show()

#שליפת אנשים בתנאים מסויימים
# tall_and_light = df[(df['Height_cm'] > 180) & (df['Weight_kg'] < 70) & (df['Country'] == 'UK')]
# print(tall_and_light)

#יצירת עמודה חדשה 
# df['Height_Group'] = pd.cut(df['Height_cm'], bins = [0, 165, 180, 250], labels = ['Short', 'Medium', 'Tall'])
# print(df)

#יצירת היסטוגרמה
# plt.figure(figsize = (8, 5))
# plt.hist(df['Height_cm'], bins = 10, color = 'skyblue', edgecolor = 'black')
# plt.title('Height Distribution')
# plt.xlabel('Height (cm)')
# plt.ylabel('Number of People')
# plt.grid(axis = 'y', linestyle = '--', alpha = 0.7)
# plt.tight_layout()
# plt.show()

# יצירת בוקספלוס

filtered_df = df[df['Country'].isin(['USA', 'UK'])]
# plt.figure(figsize=(5,5))
# sns.boxplot(data = filtered_df, x = 'Country', y = 'Weight_kg', color = 'skyblue')
# plt.title('Weight Comparison (USA vs UK)')
# plt.ylabel('Weight (kg)')
# plt.grid(axis= 'y', linestyle = '--', alpha = 0.5)
# plt.tight_layout()
# plt.show()

#יצירת מפת חום
# corr_matrix = df[['Height_cm', 'Weight_kg']].corr()
# plt.figure(figsize=(6, 5))
# sns.heatmap(corr_matrix, annot = True, cmap = 'coolwarm', vmin= -1, vmax= 1, fmt= ' .2f')
# plt.title('Correlation Heatmap')
# plt.tight_layout()
# plt.show()


nums = [1,2,3,4,5,6,7,8,9,10]
num = random.choice(nums)
x = 0
while x != num:
    x = int(input('enter number 1 to 10: '))
    print('try again')
print('good job')




