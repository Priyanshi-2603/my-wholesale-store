import streamlit as st
import json
import urllib.parse
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

# ---------------- LOAD PRODUCTS ----------------
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------- SESSION INIT ----------------
if "cart" not in st.session_state:
    st.session_state.cart = []

if "page" not in st.session_state:
    st.session_state.page = "shop"


# ---------------- UPDATE CART FUNCTION ----------------
def update_cart(product_name, size, price, dozens, image):

    # Remove existing same product+size
    st.session_state.cart = [
        item
        for item in st.session_state.cart
        if not (item["product"] == product_name and item["size"] == size)
    ]

    if dozens > 0:
        item = {
            "product": product_name,
            "size": size,
            "dozens": dozens,
            "quantity": dozens * 12,
            "total_price": price * 12 * dozens,
            "image": image,
        }
        st.session_state.cart.append(item)


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


# ========================= SHOP PAGE =========================
if st.session_state.page == "shop":

    st.title("🛍 Shri Girraj Mukut Shringar Kendra")

    category = st.selectbox("Select Category", list(data.keys()))
    subcategory_list = list(data[category].keys())
    subcategory = st.selectbox("Select Subcategory", ["All"] + subcategory_list)

    products_by_sub = (
        data[category]
        if subcategory == "All"
        else {subcategory: data[category][subcategory]}
    )

    search = st.text_input("🔍 Search Product Name")

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
                        "Select Size", list(prices.keys()), key=f"{p['id']}_size"
                    )

                    price = prices[size]
                    input_key = f"{p['id']}_{size}"

                    def quantity_changed(product=p, size=size, price=price):
                        dozens_value = st.session_state[input_key]
                        update_cart(
                            product["name"], size, price, dozens_value, product["image"]
                        )

                    dozens = st.number_input(
                        "Quantity (dozens)",
                        min_value=0,
                        value=0,
                        step=1,
                        key=input_key,
                        on_change=quantity_changed,
                    )

                    if dozens > 0:
                        st.write(f"Total: ₹{price * 12 * dozens}")

            idx += 1

    total = sum(item["total_price"] for item in st.session_state.cart)

    if total > 0:
        st.markdown("---")
        st.subheader(f"🛒 Cart Total: ₹{total}")

        if st.button("🛒 Place Order"):
            st.session_state.page = "checkout"


# ========================= CHECKOUT PAGE =========================
elif st.session_state.page == "checkout":

    st.title("🧾 Checkout")

    if st.button("⬅ Back to Shop"):
        st.session_state.page = "shop"

    total = sum(item["total_price"] for item in st.session_state.cart)

    if total == 0:
        st.warning("Your cart is empty.")
        st.stop()

    customer_name = st.text_input("Customer Name")
    customer_whatsapp = st.text_input("Customer WhatsApp Number")

    st.subheader(f"Total Amount: ₹{total}")

    if st.button("✅ Confirm & Place Order"):

        if not customer_name or not customer_whatsapp:
            st.warning("Please fill all details.")
        else:

            pdf_file = generate_pdf(
                st.session_state.cart, total, customer_name, customer_whatsapp
            )

            success = send_order_email(
                st.session_state.cart, total, pdf_file, customer_name, customer_whatsapp
            )

            if success:
                st.session_state.cart = []
                st.session_state.page = "success"


# ========================= SUCCESS PAGE =========================
elif st.session_state.page == "success":

    st.success("🎉 Your Order is Placed Successfully!")
    st.info("Please send confirmation on WhatsApp.")

    business_number = "917417866405"

    message = "I have placed the order. Please check."
    encoded = urllib.parse.quote(message)
    whatsapp_url = (
        f"https://api.whatsapp.com/send?phone={business_number}&text={encoded}"
    )

    st.markdown(
        f"""
    <a href="{whatsapp_url}" target="_blank">
        <button style="
            background-color:#25D366;
            color:white;
            padding:14px 30px;
            border:none;
            border-radius:8px;
            font-size:18px;
            cursor:pointer;">
            Send Confirmation on WhatsApp
        </button>
    </a>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🏠 Back to Shop"):
        st.session_state.page = "shop"
