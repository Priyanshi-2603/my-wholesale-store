import streamlit as st
import json
import os

st.set_page_config(page_title="Business Catalogue", layout="wide")

# Load product data
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("🛍 Business Product Catalogue")
st.write("Select category → subcategory → product")

# Sidebar Category
category = st.sidebar.selectbox("Select Category", list(data.keys()))

subcategory_list = list(data[category].keys())
subcategory = st.sidebar.selectbox("Select Subcategory", subcategory_list)

products = data[category][subcategory]

st.subheader(f"📌 Category: {category.upper()}  |  Subcategory: {subcategory.replace('_',' ').upper()}")
st.write("---")

# Search
search = st.text_input("🔍 Search Product Name")

filtered_products = []
for p in products:
    if search.lower() in p["name"].lower():
        filtered_products.append(p)

# Show Products
cols = st.columns(3)

for i, product in enumerate(filtered_products):
    with cols[i % 3]:
        st.markdown(f"### {product['name']}")
       # st.markdown(f"**Price:** {product['price']}")

        img_path = os.path.join("images", product["image"])
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning("Image not found. Add it in images/ folder.")

        st.write(product["description"])
        st.markdown("---")

