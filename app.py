import streamlit as st

# Page Configuration
st.set_page_config(page_title="Shri Girraj Mukut Shringar Kendra", page_icon="🙏", layout="wide")

# 1. Product Database (Categories ke saath)
# Aap yahan apne products add kar sakte hain
products = [
    {"category": "Poshak", "name": "Designer Kanha Poshak", "price": 120, "moq": 10, "img": "👗"},
    {"category": "Poshak", "name": "Simple Cotton Poshak", "price": 50, "moq": 50, "img": "👗"},
    {"category": "Mukut", "name": "Zardozi Mukut", "price": 80, "moq": 20, "img": "👑"},
    {"category": "Mukut", "name": "Stone Work Mukut", "price": 150, "moq": 10, "img": "👑"},
    {"category": "Lehanga Patka", "name": "Radha Rani Lehanga Set", "price": 500, "moq": 5, "img": "💃"},
    {"category": "Mala", "name": "Moti Mala Set", "price": 30, "moq": 100, "img": "📿"},
    {"category": "Mala", "name": "Tulsi Mala special", "price": 20, "moq": 200, "img": "📿"},
]

# 2. Sidebar Navigation (Categories)
st.sidebar.title("📁 Categories")
category_list = ["All", "Poshak", "Mukut", "Lehanga Patka", "Mala"]
selected_category = st.sidebar.radio("Go to:", category_list)

# 3. Main Header
st.title(f"📦 {selected_category} Collection")
st.write(f"Showing best wholesale rates for {selected_category}")

# 4. Filter Products based on Category
if selected_category == "All":
    display_products = products
else:
    display_products = [p for p in products if p["category"] == selected_category]

# 5. Display Products in Grid
cart = {}
for p in display_products:
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.title(p["img"])
        with col2:
            st.subheader(p["name"])
            st.write(f"Wholesale Price: ₹{p['price']}")
            st.caption(f"Minimum Order (MOQ): {p['moq']} units")
        with col3:
            qty = st.number_input(f"Qty", min_value=0, step=p['moq'], key=p['name'])
            if qty > 0:
                cart[p['name']] = {"qty": qty, "price": p['price']}
    st.divider()

# 6. Sidebar Cart & WhatsApp Integration
st.sidebar.header("🛒 Your Order")
if cart:
    total_bill = 0
    order_text = "Naye Order ki Details:%0A"
    for item, info in cart.items():
        st.sidebar.write(f"**{item}** x {info['qty']}")
        total_bill += info['qty'] * info['price']
        order_text += f"- {item}: {info['qty']} pcs%0A"
    
    st.sidebar.subheader(f"Total: ₹{total_bill}")
    
    # Apna Number yahan change karein
    my_number = "917417866405" 
    wa_link = f"https://wa.me/{my_number}?text={order_text}%0ATotal Amount: ₹{total_bill}"
    
    st.sidebar.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">Order on WhatsApp</button></a>', unsafe_allow_html=True)
else:
    st.sidebar.info("Cart is empty. Select products to order.")


