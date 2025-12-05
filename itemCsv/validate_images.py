import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def check_image_exists(url, timeout=5):
    """
    Check if an image URL is accessible.
    Returns (True/False, url, error_message)
    """
    if pd.isna(url) or not url or url.strip() == '':
        return (False, url, "Empty URL")
    
    try:
        # Try HEAD first (faster)
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image' in content_type:
                return (True, url, None)
        
        # If HEAD doesn't work or returns non-200, try GET with stream
        response = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image' in content_type:
                return (True, url, None)
            else:
                return (False, url, f"Not an image (Content-Type: {content_type})")
        else:
            return (False, url, f"HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        return (False, url, "Timeout")
    except requests.exceptions.ConnectionError:
        return (False, url, "Connection error")
    except requests.exceptions.InvalidURL:
        return (False, url, "Invalid URL")
    except Exception as e:
        return (False, url, str(e))
    
    return (False, url, "Unknown error")

# Read the CSV file
print("Reading CSV file...")
df = pd.read_csv("DemoITems.csv")

print(f"Original number of items: {len(df)}")
print(f"Items with image URLs: {df['Image Links'].notna().sum()}")
print(f"Items without image URLs: {df['Image Links'].isna().sum()}")

# Filter out items without image URLs first
df_with_images = df[df['Image Links'].notna()].copy()
print(f"\nItems with image URLs to validate: {len(df_with_images)}")

# Validate each image URL with parallel processing
print("\nValidating image URLs with parallel processing...")
print(f"Using 10 parallel workers\n")

valid_indices = []
invalid_count = 0
checked_count = 0
total = len(df_with_images)

# Create a list of (index, row) tuples for processing
items_to_check = [(idx, row) for idx, row in df_with_images.iterrows()]

def process_item(item):
    idx, row = item
    image_url = row['Image Links']
    plu = row['PLU']
    name = row['Name'][:40] if pd.notna(row['Name']) else 'N/A'
    return (idx, plu, name, image_url, check_image_exists(image_url))

# Process in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit all tasks
    future_to_item = {executor.submit(process_item, item): item for item in items_to_check}
    
    # Process completed tasks
    for future in as_completed(future_to_item):
        checked_count += 1
        try:
            idx, plu, name, image_url, (is_valid, url, error) = future.result()
            
            if is_valid:
                valid_indices.append(idx)
                print(f"[{checked_count}/{total}] ✅ PLU {plu}: Valid image")
            else:
                invalid_count += 1
                error_msg = f" - {error}" if error else ""
                print(f"[{checked_count}/{total}] ❌ PLU {plu}: Invalid image{error_msg}")
                print(f"         Name: {name}")
                print(f"         URL: {image_url[:70]}...")
        except Exception as e:
            checked_count += 1
            invalid_count += 1
            idx, row = future_to_item[future]
            print(f"[{checked_count}/{total}] ❌ PLU {row['PLU']}: Exception - {str(e)}")
        
        # Show progress every 10 items
        if checked_count % 10 == 0:
            print(f"\n📊 Progress: {checked_count}/{total} checked | ✅ {len(valid_indices)} valid | ❌ {invalid_count} invalid\n")

# Keep only items with valid images
df_valid = df_with_images.loc[valid_indices].copy()

# Also keep items that didn't have image URLs (if you want to keep them)
# Or remove them - let's remove them for now
# If you want to keep items without image URLs, uncomment the next line:
# df_valid = pd.concat([df_valid, df[df['Image Links'].isna()]])

print(f"\n{'='*60}")
print(f"📊 VALIDATION SUMMARY")
print(f"{'='*60}")
print(f"  ✅ Valid images: {len(valid_indices)}")
print(f"  ❌ Invalid images: {invalid_count}")
print(f"  📭 Items without URLs: {df['Image Links'].isna().sum()}")
print(f"  📦 Total original items: {len(df)}")
print(f"  📦 Items to keep: {len(df_valid)}")
print(f"  🗑️  Items to remove: {len(df) - len(df_valid)}")
print(f"{'='*60}\n")

# Save the filtered CSV
print("💾 Saving filtered CSV...")
df_valid.to_csv("DemoITems.csv", index=False)
print(f"✅ Saved filtered data to DemoITems.csv")
print(f"   Removed {len(df) - len(df_valid)} items")
print(f"   Kept {len(df_valid)} items with valid images")

