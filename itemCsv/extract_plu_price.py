import pandas as pd

# Read the CSV file
df = pd.read_csv("DemoITems.csv")

# Extract only PLU and Base Price columns
extracted_df = pd.DataFrame({
    'plu': df['PLU'],
    'price': df['Base Price']
})

# Save to new CSV file
output_path = "PLU_Price.csv"
extracted_df.to_csv(output_path, index=False)

print(f"✓ Created {output_path} with {len(extracted_df)} items")
print(f"Columns: {list(extracted_df.columns)}")
print(f"\nFirst 5 rows:")
print(extracted_df.head())

