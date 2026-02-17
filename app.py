import streamlit as st
import json
import os

st.set_page_config(page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide")

# Load product data
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🛍 Shri Girraj Mukut Shringar Kendra Product Catalogue")
#st.write("Product Catalogue")

# Sidebar Category
category = st.sidebar.selectbox("Select Category", list(data.keys()))

# Subcategory select should allow showing ALL subcategories when chosen
subcategory_list = list(data[category].keys())
subcategory_options = ["All"] + subcategory_list
subcategory = st.sidebar.selectbox("Select Subcategory", subcategory_options)

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
cols = st.columns(3)
idx = 0
for sub_name, products in products_by_sub.items():
    # Optional small header for each subcategory when showing all
    if subcategory == "All":
        st.markdown(f"**{sub_name.replace('_',' ').title()}**")

    for p in products:
        if search and search.strip() != "":
            if search.lower() not in p.get("name", "").lower():
                continue

        with cols[idx % 3]:
            st.markdown(f"### {p.get('name','Unnamed')}")
            img_path = os.path.join("images", p.get("image", ""))
            if os.path.exists(img_path):
                st.image(img_path, width='stretch')
            else:
                st.warning("Image not found. Add it in images/ folder.")

            st.write(p.get("description", ""))
            st.markdown("---")

        idx += 1

