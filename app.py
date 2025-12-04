import streamlit as st
import pandas as pd
import io
from inventoryUpload.inveUpload import request_signed_url, upload_csv
from authentication.tokening import getHeaders
from datetime import datetime

def convert_to_upload_format(df_or_series, location="Times Square"):
    """
    Convert product catalog to Deliverect inventory upload format.
    Format: location | plu | stock status | stock | price
    """
    # Handle both single row (Series) and DataFrame
    if isinstance(df_or_series, pd.Series):
        # Single product
        upload_df = pd.DataFrame({
            'location': [location],
            'plu': [df_or_series['PLU']],
            'stock status': [df_or_series['Stock Status']],
            'stock': [df_or_series['Stock Quantity']],
            'price': [df_or_series['Base Price']]
        })
    else:
        # Multiple products
        upload_df = pd.DataFrame({
            'location': location,
            'plu': df_or_series['PLU'],
            'stock status': df_or_series['Stock Status'],
            'stock': df_or_series['Stock Quantity'],
            'price': df_or_series['Base Price']
        })
    return upload_df

# Page configuration
st.set_page_config(
    page_title="DPOS | Inventory Management System",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for POS/ERP styling
st.markdown("""
    <style>
    /* Header styling */
    .pos-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-in-stock {
        background-color: #28a745;
        color: white;
    }
    
    .status-out-of-stock {
        background-color: #dc3545;
        color: white;
    }
    
    /* Sidebar styling - adapts to theme */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.02);
        border-right: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] {
            background-color: rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# Load CSV data
@st.cache_data
def load_data():
    df = pd.read_csv("itemCsv/DemoITems.csv")
    
    # Add stock management columns if they don't exist
    if 'Stock Status' not in df.columns:
        df['Stock Status'] = 'IN_STOCK'
    if 'Stock Quantity' not in df.columns:
        df['Stock Quantity'] = 10
    
    return df

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()
if 'modified_items' not in st.session_state:
    st.session_state.modified_items = set()
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

# Header
st.markdown(f"""
    <div class="pos-header">
        <h1 style="margin: 0; font-size: 2rem;">🏪 Deliverect ERP - Inventory Management System</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Real-time inventory control & synchronization</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    # Prominent configuration section
    st.markdown("""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            text-align: center;
        '>
            <h2 style='color: white; margin: 0; font-size: 1.5rem;'>⚙️ Configuration</h2>
            <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
                Connect to Deliverect
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Account Configuration with helper text
    st.markdown("**🔗 Account Settings**")
    account_id = st.text_input(
        "Account ID",
        value="",
        placeholder="Enter Deliverect Account ID"
    )

    st.markdown("---")
    st.caption("📍 Location: Times Square")

    
    # Hidden settings (still needed for functionality)
    location = "Times Square"  # Default location
    callback_url = "https://example.com/callback"  # Default callback URL

# Main content area - Table View
# Toolbar
toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 2])

with toolbar_col1:
    search_term = st.text_input("🔍 Search Products", placeholder="Product name, PLU, or category...")

with toolbar_col2:
    category_filter = st.selectbox("Category", ["All"] + sorted(st.session_state.df['Category 1'].unique().tolist()))

with toolbar_col3:
    stock_filter = st.selectbox("Stock", ["All", "IN_STOCK", "OUT_OF_STOCK"])

with toolbar_col4:
    items_per_page = st.selectbox("Items per page", [20, 50, 100], index=0)

# Sync button at top
if len(st.session_state.modified_items) > 0:
    st.markdown("")
    sync_col1, sync_col2, sync_col3 = st.columns([2, 2, 2])
    with sync_col2:
        if st.button(f"🚀 SYNC {len(st.session_state.modified_items)} ITEMS TO DELIVERECT", type="primary", use_container_width=True, key="sync_top"):
            if not account_id:
                st.error("⚠️ Account ID required")
            else:
                try:
                    with st.spinner(f"⏳ Syncing {len(st.session_state.modified_items)} items..."):
                        # Get all modified products
                        modified_products = st.session_state.df.loc[list(st.session_state.modified_items)]
                        
                        # Convert to upload format
                        upload_df = convert_to_upload_format(modified_products, location)
                        
                        # Convert to CSV
                        csv_buffer = io.StringIO()
                        upload_df.to_csv(csv_buffer, index=False)
                        csv_text = csv_buffer.getvalue()
                        
                        # Upload
                        signed_url, upload_headers, file_id = request_signed_url(account_id, callback_url)
                        upload_csv(csv_text, signed_url, upload_headers)
                        
                        # Clear modifications and update sync time
                        st.session_state.modified_items.clear()
                        st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        st.success(f"✅ Successfully synced {len(modified_products)} items!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Sync failed: {str(e)}")

st.markdown("---")

# Apply filters
filtered_df = st.session_state.df.copy()

if search_term:
    filtered_df = filtered_df[
        filtered_df['Name'].str.contains(search_term, case=False, na=False) |
        filtered_df['PLU'].astype(str).str.contains(search_term, case=False)
    ]

if category_filter != "All":
    filtered_df = filtered_df[filtered_df['Category 1'] == category_filter]

if stock_filter != "All":
    filtered_df = filtered_df[filtered_df['Stock Status'] == stock_filter]

total_filtered = len(filtered_df)

# Pagination
total_pages = (total_filtered - 1) // items_per_page + 1 if total_filtered > 0 else 1
current_page = st.session_state.current_page

# Get page data
start_idx = current_page * items_per_page
end_idx = start_idx + items_per_page
page_data = filtered_df.iloc[start_idx:end_idx]

# Show item count at top
st.markdown(f"**Showing {min(current_page * items_per_page + 1, total_filtered)} - {min((current_page + 1) * items_per_page, total_filtered)} of {total_filtered} items**")
st.markdown("")

# Table header
header_cols = st.columns([3, 1, 1, 1, 1, 1, 1])
with header_cols[0]:
    st.markdown("**PRODUCT**")
with header_cols[1]:
    st.markdown("**CATEGORY**")
with header_cols[2]:
    st.markdown("**PLU**")
with header_cols[3]:
    st.markdown("**PRICE ($)**")
with header_cols[4]:
    st.markdown("**STOCK**")
with header_cols[5]:
    st.markdown("**STATUS**")
with header_cols[6]:
    st.markdown("**ACTIONS**")

st.markdown("---")

# Table rows
for idx, row in page_data.iterrows():
    is_modified = idx in st.session_state.modified_items
    
    row_cols = st.columns([3, 1, 1, 1, 1, 1, 1])
    
    with row_cols[0]:
        st.markdown(f"{'🔶 ' if is_modified else ''}{row['Name'][:45]}{'...' if len(row['Name']) > 45 else ''}")
    
    with row_cols[1]:
        st.text(row['Category 1'][:15])
    
    with row_cols[2]:
        st.text(str(row['PLU']))
    
    with row_cols[3]:
        new_price = st.number_input(
            "Price",
            min_value=0.0,
            value=float(row['Base Price']),
            step=0.01,
            format="%.2f",
            key=f"price_{idx}",
            label_visibility="collapsed"
        )
        if new_price != float(row['Base Price']):
            st.session_state.df.at[idx, 'Base Price'] = new_price
            st.session_state.modified_items.add(idx)
    
    with row_cols[4]:
        new_stock = st.number_input(
            "Stock",
            min_value=0,
            value=int(row['Stock Quantity']),
            step=1,
            key=f"stock_{idx}",
            label_visibility="collapsed"
        )
        if new_stock != int(row['Stock Quantity']):
            st.session_state.df.at[idx, 'Stock Quantity'] = new_stock
            st.session_state.modified_items.add(idx)
    
    with row_cols[5]:
        new_status = st.selectbox(
            "Status",
            options=["IN_STOCK", "OUT_OF_STOCK"],
            index=0 if row['Stock Status'] == 'IN_STOCK' else 1,
            key=f"status_{idx}",
            label_visibility="collapsed"
        )
        if new_status != row['Stock Status']:
            st.session_state.df.at[idx, 'Stock Status'] = new_status
            st.session_state.modified_items.add(idx)
    
    with row_cols[6]:
        if is_modified:
            if st.button("↺", key=f"revert_{idx}", help="Revert changes"):
                # Reload original data for this row
                original_df = load_data()
                st.session_state.df.loc[idx] = original_df.loc[idx]
                st.session_state.modified_items.discard(idx)
                st.rerun()
        else:
            st.text("")
    
    st.divider()

st.markdown("---")

# Modern page navigation at bottom
st.markdown("""
    <style>
    .pagination-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        gap: 1rem;
    }
    .page-info {
        opacity: 0.7;
        font-size: 0.9rem;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns([2, 3, 2])

with nav_col1:
    st.markdown(f'<div class="page-info">Showing <strong>{min(current_page * items_per_page + 1, total_filtered):,}</strong> to <strong>{min((current_page + 1) * items_per_page, total_filtered):,}</strong> of <strong>{total_filtered:,}</strong> items</div>', unsafe_allow_html=True)

with nav_col2:
    # Modern pagination controls with custom styling
    st.markdown("""
        <style>
        /* Custom pagination button styling - adapts to theme */
        div[data-testid="column"] > div > div > button[kind="secondary"] {
            border-radius: 8px;
            border: 1px solid rgba(102, 126, 234, 0.3);
            background: rgba(102, 126, 234, 0.05);
            color: #667eea;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        div[data-testid="column"] > div > div > button[kind="secondary"]:hover {
            background: rgba(102, 126, 234, 0.15);
            border-color: #667eea;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.25);
        }
        div[data-testid="column"] > div > div > button[kind="secondary"]:disabled {
            background: rgba(0, 0, 0, 0.05);
            color: rgba(102, 126, 234, 0.3);
            border-color: rgba(0, 0, 0, 0.1);
            cursor: not-allowed;
            opacity: 0.5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    page_cols = st.columns([1, 1, 2, 1, 1])
    with page_cols[0]:
        if st.button("⏮ First", disabled=current_page == 0, key="first_bottom", use_container_width=True, type="secondary"):
            st.session_state.current_page = 0
            st.rerun()
    with page_cols[1]:
        if st.button("◀ Prev", disabled=current_page == 0, key="prev_bottom", use_container_width=True, type="secondary"):
            st.session_state.current_page -= 1
            st.rerun()
    with page_cols[2]:
        st.markdown(f"""
            <div style='
                text-align: center; 
                padding: 0.75rem 1rem; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 0.95rem;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
                letter-spacing: 0.5px;
            '>
                Page {current_page + 1} of {total_pages}
            </div>
        """, unsafe_allow_html=True)
    with page_cols[3]:
        if st.button("Next ▶", disabled=current_page >= total_pages - 1, key="next_bottom", use_container_width=True, type="secondary"):
            st.session_state.current_page += 1
            st.rerun()
    with page_cols[4]:
        if st.button("Last ⏭", disabled=current_page >= total_pages - 1, key="last_bottom", use_container_width=True, type="secondary"):
            st.session_state.current_page = total_pages - 1
            st.rerun()

with nav_col3:
    if len(st.session_state.modified_items) > 0:
        st.markdown(f'<div style="text-align: center; padding: 0.5rem; color: #667eea; font-weight: 600;">📝 {len(st.session_state.modified_items)} items modified</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align: center; opacity: 0.5; padding: 0.5rem;">No changes</div>', unsafe_allow_html=True)

# Summary footer
if len(st.session_state.modified_items) > 0:
    st.markdown("---")
    st.info(f"📝 **{len(st.session_state.modified_items)} items modified** - Scroll to top to sync changes to Deliverect")
