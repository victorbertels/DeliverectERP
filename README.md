# Product Inventory Manager

A Streamlit application for managing product inventory and syncing with Deliverect.

## Features

- 🔍 **Search Products**: Search through your product catalog by name
- ✏️ **Edit Details**: Update product price, stock status, and stock quantity
- 🚀 **Push to Deliverect**: Sync your changes directly to Deliverect via their API
- 📥 **Export CSV**: Download your updated inventory as a CSV file

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure credentials**:
Create a `.env` file in the project root with your Deliverect credentials:
```
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
```

3. **Prepare your CSV**:
Place your product CSV file at `itemCsv/DemoITems.csv`

## Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Configure Settings**: In the sidebar, enter:
   - Account ID (Deliverect Account ID)
   - Location (location identifier for inventory)
   - Callback URL (optional)
2. **Search Product**: Use the search box to find products by name
3. **Select Product**: Click "Select" on a product to view and edit its details
4. **Update Fields**:
   - Base Price
   - Stock Status (IN_STOCK, OUT_OF_STOCK, LOW_STOCK)
   - Stock Quantity
5. **Preview**: Expand "Preview Upload Format" to see how data will be sent
6. **Save Changes**: Click "Save Changes" to update locally
7. **Push to Deliverect**: Click "Push to Deliverect" to sync with the API

### Upload Format

When pushing to Deliverect, the CSV is converted to the required format:
```
location | PLU | Stock status | Stock quantity | Price
```

This tab-separated format contains only the essential inventory data needed by Deliverect.

## Project Structure

```
VPOS/
├── app.py                          # Main Streamlit application
├── authentication/
│   ├── tokening.py                 # OAuth token management
│   └── filter_items.py             # CSV filtering utility
├── inventoryUpload/
│   └── inveUpload.py               # Deliverect API integration
├── itemCsv/
│   └── DemoITems.csv               # Product catalog
└── requirements.txt                # Python dependencies
```

## API Integration

The app uses Deliverect's Inventory Upload API:
- Requests a signed URL for CSV upload
- Uploads the entire updated catalog
- Provides callback URL for upload status

## Notes

- Changes are saved locally in the session first
- Pushing to Deliverect uploads the entire catalog, not just changes
- Stock Status and Stock Quantity columns are automatically added if not present

# DeliverectERP
