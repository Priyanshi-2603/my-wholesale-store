import streamlit as st
import json
import urllib.parse
import pandas as pd

# from streamlit_local_storage import LocalStorage
import io
import requests
import base64
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide"
)

st.markdown(
    """
<style>
.sticky-cart {
position: fixed;
bottom: 20px;
right: 20px;
z-index: 999;
}
</style>
""",
    unsafe_allow_html=True,
)


def cart_total():
    return sum(
        item.get("total_price", 0)
        for item in st.session_state.cart
        if isinstance(item, dict)
    )


# ---------------- SESSION PAGE CONTROL ----------------
if "page" not in st.session_state:
    st.session_state.page = "shop"

# # Safety initialization for cart
# if "cart" not in st.session_state:
#     st.session_state.cart = []

# ---------------- LOAD PRODUCTS ----------------
# with open("products.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# ---------------- LOAD PRODUCTS FROM GOOGLE SHEET ----------------


@st.cache_data(ttl=3600)
def load_products():

    sheet_url = "https://docs.google.com/spreadsheets/d/1UeAOfwUV7YkEGM-jQXNJZ8Nd3_nJGERUyqvlXWuRb50/export?format=csv"

    df = pd.read_csv(sheet_url)

    # Clean column names
    df.columns = df.columns.str.strip().str.lower()

    data = {}

    grouped = df.groupby(["category", "subcategory", "name", "image", "unit", "id"])

    for (cat, sub, name, image, unit, pid), group in grouped:

        first = group.iloc[0]

        prices = dict(zip(group["size"], group["price"]))

        product = {
            "id": int(first["id"]),
            "name": name,
            "image": first["image"],
            "unit": int(first["unit"]),
            "prices": prices,
        }

        if cat not in data:
            data[cat] = {}

        if sub not in data[cat]:
            data[cat][sub] = []

        data[cat][sub].append(product)

    return data


data = load_products()


# ---------------- LOAD CART FROM QUERY PARAM ----------------
query_params = st.query_params
if "page" in query_params:
    st.session_state.page = query_params["page"]


if "cart" not in st.session_state:

    if "cart" in query_params:
        try:
            st.session_state.cart = json.loads(query_params["cart"])
        except:
            st.session_state.cart = []
    else:
        st.session_state.cart = []

# ---------------- LOAD CART ----------------

# if "cart" not in st.session_state:
#     saved_cart = local_storage.getItem("cart")
#     st.session_state.cart = json.loads(saved_cart) if saved_cart else []

# ---------------- PRODUCT ADD SUCCESS TRACKER ----------------
if "added_product" not in st.session_state:
    st.session_state.added_product = None


# ---------------- ADD TO CART ----------------
def add_to_cart(product_id, product_name, size, price, qty, image, unit):

    # Remove same product+size first
    st.session_state.cart = [
        item
        for item in st.session_state.cart
        if isinstance(item, dict)
        and not (item.get("product") == product_name and item.get("size") == size)
    ]

    quantity = qty * unit
    total_price = price * unit * qty

    item = {
        "product": product_name,
        "size": size,
        "dozens": qty,
        "quantity": quantity,
        "total_price": total_price,
        "image": image,
    }

    st.session_state.cart.append(item)
    st.query_params["cart"] = json.dumps(st.session_state.cart)

    # Store which product was added
    st.session_state.added_product = product_id


def increase_qty(index):
    item = st.session_state.cart[index]
    unit = item["quantity"] // item["dozens"]

    item["dozens"] += 1
    item["quantity"] = item["dozens"] * unit
    item["total_price"] = item["total_price"] / (item["dozens"] - 1) * item["dozens"]

    st.session_state.cart[index] = item
    st.query_params["cart"] = json.dumps(st.session_state.cart)
    st.rerun()


def decrease_qty(index):
    item = st.session_state.cart[index]

    if item["dozens"] > 1:
        unit = item["quantity"] // item["dozens"]

        item["dozens"] -= 1
        item["quantity"] = item["dozens"] * unit
        item["total_price"] = (
            item["total_price"] / (item["dozens"] + 1) * item["dozens"]
        )

        st.session_state.cart[index] = item
        st.query_params["cart"] = json.dumps(st.session_state.cart)

    else:
        remove_item(index)

    st.rerun()


def remove_item(index):
    st.session_state.cart.pop(index)
    st.query_params["cart"] = json.dumps(st.session_state.cart)
    st.rerun()


# ---------------- PDF GENERATION ----------------
def generate_pdf(cart_items, total, name, whatsapp):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Shri Girraj Mukut Shringar Kendra", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Customer Name: {name}", styles["Normal"]))
    elements.append(Paragraph(f"WhatsApp: {whatsapp}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    for item in cart_items:
        elements.append(
            Paragraph(f"<b>Product:</b> {item['product']}", styles["Normal"])
        )
        elements.append(Paragraph(f"Size: {item['size']}", styles["Normal"]))
        elements.append(
            Paragraph(
                f"Quantity: {item['dozens']} dozen ({item['quantity']} pcs)",
                styles["Normal"],
            )
        )
        elements.append(Paragraph(f"Total: ₹{item['total_price']}", styles["Normal"]))
        elements.append(Spacer(1, 6))

        try:
            response = requests.get(item["image"])
            img_data = io.BytesIO(response.content)
            img = Image(img_data, width=2 * inch, height=2 * inch)
            elements.append(img)
        except:
            elements.append(Paragraph("Image not available", styles["Normal"]))

        elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Final Amount: ₹{total}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Delivery Charges: Not Included", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------- EMAIL FUNCTION ----------------
def send_order_email(cart_items, total, pdf_buffer, name, whatsapp):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = st.secrets["BREVO_API_KEY"]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    html_content = f"""
    <h2>New Order Received</h2>
    <p><b>Customer Name:</b> {name}</p>
    <p><b>WhatsApp:</b> {whatsapp}</p>
    <hr>
    """

    for item in cart_items:
        html_content += f"""
        <div style="margin-bottom:20px;">
            <img src="{item['image']}" width="150"><br>
            <b>Product:</b> {item['product']}<br>
            <b>Size:</b> {item['size']}<br>
            <b>Quantity:</b> {item['dozens']} dozen ({item['quantity']} pcs)<br>
            <b>Total:</b> ₹{item['total_price']}<br>
        </div>
        """

    html_content += f"<h3>Final Amount: ₹{total}</h3>"

    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": st.secrets["RECEIVER_EMAIL"]}],
        sender={"email": st.secrets["SENDER_EMAIL"]},
        subject="New Order - Shri Girraj Mukut Shringar Kendra",
        html_content=html_content,
        attachment=[{"content": pdf_base64, "name": "order_summary.pdf"}],
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        return True
    except ApiException as e:
        st.error(f"Email sending failed: {e}")
        return False


# ============================================================
# ================= SHOP PAGE ================================
# ============================================================

if st.session_state.page == "shop":

    st.title("🛍 Shri Girraj Mukut Shringar Kendra")

    # Show success message once
    if "last_added" in st.session_state:
        st.success(f"✅ {st.session_state.last_added} added to cart successfully!")
        del st.session_state.last_added

    # ---------- TOP CART BAR ----------
    total = cart_total()

    col1, col2, col3 = st.columns([4, 1.5, 1.5])

    with col1:
        if total > 0:
            st.markdown(f"### 🛒 Cart Total: ₹{total}")
        else:
            st.markdown("### 🛒 Cart is Empty")

    with col2:
        if total > 0:
            if st.button(f"🛍 Place Order (₹{total})"):
                st.session_state.page = "checkout"
                st.rerun()

    with col3:
        if total > 0:
            if st.button("❌ Clear Cart"):
                st.query_params["cart"] = json.dumps([])
                st.session_state.cart = []
                st.query_params["cart"] = json.dumps([])
                st.success("Cart Cleared Successfully")
                st.rerun()

    st.markdown("---")
    category = st.selectbox("Select Category", list(data.keys()))
    subcategory_list = list(data[category].keys())
    subcategory = st.selectbox("Select Subcategory", ["All"] + subcategory_list)

    products_by_sub = (
        data[category]
        if subcategory == "All"
        else {subcategory: data[category][subcategory]}
    )

    search = st.text_input("🔍 Search Product")

    for sub_name, products in products_by_sub.items():

        st.markdown(f"### {sub_name}")
        cols = st.columns(2)
        idx = 0

        for p in products:

            if search and search.lower() not in p["name"].lower():
                continue

            with cols[idx % 2]:

                st.markdown(f"### {p['name']}")

                if p.get("image"):
                    st.image(p["image"], use_container_width=True)

                prices = p.get("prices", {})
                if prices:

                    size = st.selectbox(
                        "Select Size", list(prices.keys()), key=f"{p['id']}_{idx}_size"
                    )

                    price = prices[size]

                    dozens = st.number_input(
                        "Select Quantity (dozens)",
                        min_value=1,
                        value=1,
                        key=f"{p['id']}_{idx}_qty",
                    )

                    unit = p.get("unit", 12)

                    # 👇 ADD THIS HERE
                    per_piece_price = price
                    pack_price = price * unit

                    st.write(f"💰 Price per piece: ₹{per_piece_price}")
                    st.write(f"📦 Minimum Packing: {unit} pcs")
                    st.write(f"📦 Price per pack: ₹{pack_price}")

                    st.write(f"🧾 Total Price: ₹{pack_price * dozens}")

                    if st.button("Add to Cart", key=f"add_{p['id']}_{idx}"):
                        unit = p.get("unit", 12)
                        add_to_cart(
                            p["id"], p["name"], size, price, dozens, p["image"], unit
                        )
                        st.success("Added to cart ✅")
                        st.rerun()

                    if st.session_state.get("added_product") == p["id"]:
                        st.success("✅ Added to cart successfully!")
                        st.session_state.added_product = None

            idx += 1

    # Floating Place Order Button
    # if len(st.session_state.cart) > 0:
    #     st.markdown("---")
    #     if st.button("🛒 Place Order"):
    #         st.session_state.page = "checkout"
    #         st.rerun()
if len(st.session_state.cart) > 0:

    total = cart_total()
    cart_data = urllib.parse.quote(json.dumps(st.session_state.cart))

    st.markdown(
        f"""
        <div class="sticky-cart">
            <a href="?page=checkout&cart={cart_data}">
                <button style="
                background-color:#ff4b4b;
                color:white;
                padding:15px 25px;
                font-size:18px;
                border:none;
                border-radius:10px;
                cursor:pointer;">
                🛒 Checkout ₹{total}
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# if len(st.session_state.cart) > 0:

#     total = cart_total()

#     st.markdown('<div class="sticky-cart">', unsafe_allow_html=True)

#     if st.button(f"🛒 Checkout ₹{total}", key="checkout_btn"):
#         st.session_state.page = "checkout"
#         st.rerun()

#     st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# ================= CHECKOUT PAGE ============================
# ============================================================

if st.session_state.page == "checkout":

    st.title("🧾 Checkout Page")

    if st.button("⬅ Back to Shop"):
        st.session_state.page = "shop"
        st.query_params.clear()
        st.rerun()

    st.markdown("---")

    customer_name = st.text_input("Customer Name")
    customer_whatsapp = st.text_input("Customer WhatsApp Number")

    if len(st.session_state.cart) > 0:

        st.subheader("🛒 Order Summary")

        for i, item in enumerate(st.session_state.cart):

            col1, col2 = st.columns([1, 3])

            with col1:
                if item.get("image"):
                    st.image(item["image"], width=120)

            with col2:

                pcs_price = item["total_price"] / item["quantity"]

                st.write(f"**Product:** {item['product']}")
                st.write(f"Size: {item['size']}")
                st.write(f"Price per pcs: ₹{round(pcs_price,2)}")

                colA, colB, colC, colD = st.columns([1, 1, 2, 1])

                with colA:
                    if st.button("➖", key=f"dec_{i}"):
                        decrease_qty(i)

                with colB:
                    st.write(f"{item['dozens']} pack")

                with colC:
                    if st.button("➕", key=f"inc_{i}"):
                        increase_qty(i)

                with colD:
                    if st.button("🗑", key=f"del_{i}"):
                        remove_item(i)

                st.write(f"Quantity: {item['quantity']} pcs")
                st.write(f"Total: ₹{item['total_price']}")

            st.markdown("---")

    total = cart_total()
    st.subheader(f"Final Amount: ₹{total}")

    if st.button("✅ Place Order Now"):

        if not customer_name or not customer_whatsapp:
            st.warning("Please fill all details before placing order.")
        else:

            pdf_file = generate_pdf(
                st.session_state.cart, total, customer_name, customer_whatsapp
            )

            success = send_order_email(
                st.session_state.cart,
                total,
                pdf_file,
                customer_name,
                customer_whatsapp,
            )

            if success:

                st.success("🎉 Your Order is Placed Successfully!")
                st.info("Please confirm your order on WhatsApp.")

                business_number = "917417866405"

                message = f"""
🛍 Order Placed

Name: {customer_name}
Mobile: {customer_whatsapp}
Total Amount: ₹{total}

Please confirm the order.
"""

                encoded = urllib.parse.quote(message)
                whatsapp_url = f"https://api.whatsapp.com/send?phone={business_number}&text={encoded}"

                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank">'
                    f'<button style="background-color:#25D366;color:white;'
                    f'padding:12px 25px;border:none;border-radius:6px;font-size:16px;">'
                    f"Send Order on WhatsApp"
                    f"</button></a>",
                    unsafe_allow_html=True,
                )

                st.session_state.cart = []
                # local_storage.deleteItem("cart")
                # local_storage.setItem("cart", json.dumps([]))
                st.query_params["cart"] = json.dumps([])
