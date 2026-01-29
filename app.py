import streamlit as st

# Page Configuration
st.set_page_config(page_title="My Wholesale Store", page_icon="📦")

# 1. Product Data (Aap yahan apne products dalein)
products = [
    {"name": "Cotton T-Shirts", "price": 150, "moq": 50, "image": "👕"},
    {"name": "Denim Jeans", "price": 450, "moq": 20, "image": "👖"},
    {"name": "Running Shoes", "price": 800, "moq": 10, "image": "👟"},
]

st.title("🚀 Wholesale Digital Catalog")
st.write("Welcome! Select products and place your order directly via WhatsApp.")

# 2. Sidebar for Cart
st.sidebar.header("🛒 Your Cart")
cart = {}

# 3. Main Catalog UI
for p in products:
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.title(p["image"])
        with col2:
            st.subheader(p["name"])
            st.write(f"Price: ₹{p['price']} / pc")
            st.caption(f"Minimum Order: {p['moq']} pcs")
        with col3:
            qty = st.number_input(f"Qty for {p['name']}", min_value=0, step=p['moq'], key=p['name'])
            if qty > 0:
                cart[p['name']] = {"qty": qty, "total": qty * p['price']}

st.divider()

# 4. Checkout System
if cart:
    st.sidebar.write("---")
    grand_total = 0
    order_details = "Order Details:%0A"
    
    for item, data in cart.items():
        st.sidebar.write(f"**{item}**: {data['qty']} pcs")
        grand_total += data['total']
        order_details += f"- {item}: {data['qty']} pcs%0A"
    
    st.sidebar.subheader(f"Total: ₹{grand_total}")
    
    # WhatsApp Link Generation
    phone_number = "917417866405" # <-- APNA NUMBER YAHAN DALAIN
    whatsapp_link = f"https://wa.me/{phone_number}?text={order_details}%0ATotal Amount: ₹{grand_total}"
    
    if st.sidebar.button("✅ Place Order on WhatsApp"):
        st.sidebar.markdown(f'<a href="{whatsapp_link}" target="_blank">Click here to Confirm Order</a>', unsafe_allow_items=True)
else:
    st.sidebar.write("Your cart is empty.")
