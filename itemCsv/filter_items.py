import pandas as pd

path = "/Users/victorbertels/Desktop/VPOS/itemCsv/DemoITems.csv"

# Read the CSV file
df = pd.read_csv(path)

print(f"Original number of items: {len(df)}")
print(f"\nOriginal categories breakdown:")
category_counts = df.groupby(['Category 1', 'Category 2']).size()
print(category_counts)

# Keep only 5 items per category-subcategory combination
df_filtered = df.groupby(['Category 1', 'Category 2'], group_keys=False).head(5)

print(f"\nFiltered number of items: {len(df_filtered)}")
print(f"\nFiltered categories breakdown:")
filtered_counts = df_filtered.groupby(['Category 1', 'Category 2']).size()
print(filtered_counts)

# Save the filtered data back to the same file
df_filtered.to_csv(path, index=False)
print(f"\n✓ Saved filtered data to {path}")