import streamlit as st
import json
import urllib.parse
from streamlit_local_storage import LocalStorage

st.set_page_config(
    page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide"
)

# ---------------- LOAD PRODUCT DATA ----------------
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------- BROWSER LOCAL STORAGE ----------------
local_storage = LocalStorage()

# ---------------- LOAD CART (FROM BROWSER) ----------------
if "cart" not in st.session_state:
    saved_cart = local_storage.getItem("cart")

    if saved_cart:
        st.session_state.cart = json.loads(saved_cart)
    else:
        st.session_state.cart = []


# ---------------- ADD TO CART FUNCTION ----------------
def add_to_cart(product_name, size, price, dozens, image):
    item = {
        "product": product_name,
        "size": size,
        "price_per_piece": price,
        "dozens": dozens,
        "quantity": dozens * 12,
        "total_price": price * 12 * dozens,
        "image": image,
    }

    st.session_state.cart.append(item)

    # SAVE TO BROWSER
    local_storage.setItem("cart", json.dumps(st.session_state.cart))


# ---------------- UI ----------------
st.title("🛍 Shri Girraj Mukut Shringar Kendra Product Catalogue")

# Category selection
category = st.selectbox("Select Category", list(data.keys()))
subcategory_list = list(data[category].keys())
subcategory_options = ["All"] + subcategory_list
subcategory = st.selectbox("Select Subcategory", subcategory_options)

if subcategory == "All":
    products_by_sub = {k: v for k, v in data[category].items()}
else:
    products_by_sub = {subcategory: data[category].get(subcategory, [])}

st.subheader(
    f"📌 Category: {category.upper()}  |  Subcategory: {subcategory.replace('_',' ').upper()}"
)
st.write("---")

search = st.text_input("🔍 Search Product Name")

# ---------------- DISPLAY PRODUCTS ----------------
for sub_name, products in products_by_sub.items():

    if subcategory == "All":
        st.markdown(f"### {sub_name.replace('_',' ').title()}")

    cols = st.columns(2)
    idx = 0

    for p in products:

        if search and search.lower() not in p.get("name", "").lower():
            continue

        with cols[idx % 2]:

            st.markdown(f"### {p.get('name','Unnamed')}")

            # Show image (URL supported)
            img_url = p.get("image", "")
            if img_url:
                st.image(img_url, use_column_width=True)

            prices = p.get("prices", {})

            if prices:

                unique_key = f"{category}_{sub_name}_{p['id']}"

                size = st.selectbox(
                    "Select Size", list(prices.keys()), key=f"size_{unique_key}"
                )

                price = prices[size]
                st.write(f"💵 Price per piece: ₹{price}")

                dozens = st.number_input(
                    "Select Quantity (in dozens)",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"dozen_{unique_key}",
                )

                st.write(f"Total Pieces: {dozens * 12}")
                st.write(f"Total Price: ₹{price * 12 * dozens}")

                if st.button("Add to Cart", key=f"btn_{unique_key}"):
                    add_to_cart(p["name"], size, price, dozens, img_url)
                    st.success("Added to cart ✅")

            st.markdown("---")

        idx += 1


# ================= CART SECTION =================
st.header("🛒 Cart Summary")

total = 0
order_message = "🛍 *New Order - Shri Girraj Mukut Shringar Kendra*\n\n"

for item in st.session_state.cart:
    line = (
        f"📦 *{item['product']}*\n"
        f"🖼 Image: {item['image']}\n"
        f"Size: {item['size']}\n"
        f"Quantity: {item['dozens']} dozen ({item['quantity']} pcs)\n"
        f"Amount: ₹{item['total_price']}\n\n"
    )
    order_message += line
    total += item["total_price"]

if total > 0:
    order_message += f"💰 *Final Amount:* ₹{total}\n"
    order_message += "🚚 Delivery Charges: Not Included\n"

    st.subheader(f"💰 Final Amount: ₹{total}")
    st.write("🚚 Delivery Charges Not Included")

    encoded_message = urllib.parse.quote(order_message)

    whatsapp_number = "917417866405"
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

    st.markdown(
        f'<a href="{whatsapp_url}" target="_blank">'
        f'<button style="background-color:green;color:white;padding:10px 20px;'
        f'border:none;border-radius:5px;font-size:16px;">'
        f"Place Order on WhatsApp</button></a>",
        unsafe_allow_html=True,
    )

    # Clear cart button
    if st.button("✅ Clear Cart After Order"):
        st.session_state.cart = []
        local_storage.deleteItem("cart")
        st.success("Cart Cleared Successfully 🎉")

else:
    st.info("Your cart is empty.")
