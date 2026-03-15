import streamlit as st
import json
from streamlit_local_storage import LocalStorage

st.title("Cart Demo")

local_storage = LocalStorage()

# ---------------- INIT CART ----------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# ---------------- LOAD CART FROM BROWSER ----------------
saved_cart = local_storage.getItem("cart")

if saved_cart and st.session_state.cart == []:
    try:
        st.session_state.cart = json.loads(saved_cart)
    except:
        st.session_state.cart = []

# ---------------- DISPLAY CART ----------------
st.subheader("Cart Items")

if len(st.session_state.cart) == 0:
    st.write("Cart is empty")
else:
    for item in st.session_state.cart:
        st.write("•", item)

# ---------------- ADD ITEM ----------------
product = st.text_input("Product Name")

if st.button("Add to Cart"):

    if product.strip() != "":
        st.session_state.cart.append(product)

        local_storage.setItem("cart", json.dumps(st.session_state.cart))

        st.success("Item added")

        st.rerun()

# ---------------- CLEAR CART ----------------
if st.button("Clear Cart"):

    st.session_state.cart = []

    local_storage.setItem("cart", json.dumps([]))

    st.success("Cart cleared")

    st.rerun()
