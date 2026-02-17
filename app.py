import streamlit as st
import json
import os

st.set_page_config(page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide")

# Load product data
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🛍 Shri Girraj Mukut Shringar Kendra Product Catalogue")
#st.write("Product Catalogue")

# --- add simple CSS for background and cards ---
st.markdown(
        """
        <style>
            /* page background gradient */
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(180deg, #fffaf0 0%, #f0f9ff 100%);
            }
            /* container padding */
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 2rem;
            }
            /* product card */
            .product-card {
                background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(255,255,255,0.7));
                border-radius: 12px;
                padding: 10px 12px;
                box-shadow: 0 6px 18px rgba(10,10,20,0.06);
                margin-bottom: 12px;
            }
            .product-card h3 { color: #2b2b2b; margin: 6px 0 8px 0; font-size: 18px; }
            .product-img { width: 100%; height: auto; border-radius: 8px; display:block; margin-bottom:8px; }
            /* subtle header style */
            .stHeader, .css-1v3fvcr h1 { color: #1f3b6f }
            /* category pills (select) spacing on top */
            .stSelectbox { margin-bottom: 6px }
            /* pill button styling */
            .stButton > button {
                border-radius: 20px !important;
                padding: 8px 16px !important;
                font-weight: 600 !important;
                border: none !important;
                transition: all 0.3s ease !important;
            }
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
)

# --- Horizontal pill selector for categories ---
categories = list(data.keys())
col_cat, col_space = st.columns([0.8, 0.2])
with col_cat:
    st.markdown("**Select Category:**")
    category_row = st.columns(len(categories))
    
    # Initialize session state for selected category
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = categories[0]
    
    # Render pill buttons
    for idx, cat in enumerate(categories):
        with category_row[idx]:
            is_selected = st.session_state.selected_category == cat
            button_style = "background-color: #4a7c8c; color: white; border-radius: 20px; padding: 8px 16px; font-weight: bold;" if is_selected else "background-color: #e8e8e8; color: #333; border-radius: 20px; padding: 8px 16px;"
            if st.button(cat.upper(), use_container_width=True, key=f"cat_{cat}"):
                st.session_state.selected_category = cat
                st.rerun()
    
    category = st.session_state.selected_category

# Subcategory select (also at top) — includes "All"
subcategory_list = list(data[category].keys())
subcategory_options = ["All"] + subcategory_list
subcategory = st.selectbox("Select Subcategory", subcategory_options)

if subcategory == "All":
    # Aggregate products from all subcategories for the chosen category
    products_by_sub = {k: v for k, v in data[category].items()}
else:
    products_by_sub = {subcategory: data[category].get(subcategory, [])}

st.subheader(f"📌 Category: {category.upper()}  |  Subcategory: {subcategory.replace('_',' ').upper()}")
st.write("---")

# Search
search = st.text_input("🔍 Search Product Name")

filtered_products = []

# When showing "All", iterate each subcategory and display its products
# Use 2 columns for better mobile layout, Streamlit will stack on narrow screens
cols = st.columns(2)
n_cols = len(cols)
idx = 0
for sub_name, products in products_by_sub.items():
    # Optional small header for each subcategory when showing all
    if subcategory == "All":
        st.markdown(f"**{sub_name.replace('_',' ').title()}**")

    for p in products:
        if search and search.strip() != "":
            if search.lower() not in p.get("name", "").lower():
                continue

        with cols[idx % n_cols]:
            img_rel = p.get("image", "")
            img_path = os.path.join("images", img_rel)
            if os.path.exists(img_path):
                # render a small HTML card so we can style background and image
                card = f"""
                <div class="product-card">
                  <h3>{p.get('name','Unnamed')}</h3>
                  <img src="{os.path.join('images', img_rel)}" class="product-img"/>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)
            else:
                st.markdown(f"### {p.get('name','Unnamed')}")
                st.warning("Image not found. Add it in images/ folder.")
            # descriptions were removed from the JSON; leave placeholder if needed
            desc = p.get("description", "")
            if desc:
                st.write(desc)
            st.markdown("---")

        idx += 1

