import streamlit as st
import json

st.title("Cart Demo")

# ---------------- LOAD CART ----------------
query_params = st.query_params

if "cart" not in st.session_state:
    if "cart" in query_params:
        try:
            st.session_state.cart = json.loads(query_params["cart"])
        except:
            st.session_state.cart = []
    else:
        st.session_state.cart = []

# ---------------- DISPLAY CART ----------------
st.subheader("Cart Items")

if not st.session_state.cart:
    st.write("Cart is empty")
else:
    for item in st.session_state.cart:
        st.write("•", item)

# ---------------- ADD ITEM ----------------
product = st.text_input("Product Name")

if st.button("Add to Cart"):

    if product.strip():
        st.session_state.cart.append(product)

        st.query_params["cart"] = json.dumps(st.session_state.cart)

        st.success("Item added")

        st.rerun()

# ---------------- CLEAR CART ----------------
if st.button("Clear Cart"):

    st.session_state.cart = []

    st.query_params["cart"] = json.dumps([])

    st.success("Cart cleared")

    st.rerun()
