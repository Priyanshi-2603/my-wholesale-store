import streamlit as st
import json
import urllib.parse
from streamlit_local_storage import LocalStorage
import io
import requests
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import base64


st.set_page_config(
    page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide"
)

st.write("API Key Loaded:", st.secrets["BREVO_API_KEY"])

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
                st.image(img_url, width="stretch")

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


def generate_pdf(cart_items, total_amount):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]

    elements.append(Paragraph("Shri Girraj Mukut Shringar Kendra", title_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Order Summary", styles["Heading2"]))
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

        # Add Image
        try:
            response = requests.get(item["image"])
            img_data = io.BytesIO(response.content)
            img = Image(img_data, width=2 * inch, height=2 * inch)
            elements.append(img)
        except:
            elements.append(Paragraph("Image not available", styles["Normal"]))

        elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(f"<b>Final Amount: ₹{total_amount}</b>", styles["Heading2"])
    )
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Delivery Charges: Not Included", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_order_email(cart_items, total_amount, pdf_buffer):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = st.secrets["BREVO_API_KEY"]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    html_content = "<h2>New Order Received</h2><br>"

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

    html_content += f"""
    <h3>Final Amount: ₹{total_amount}</h3>
    <p>Delivery Charges: Not Included</p>
    """

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


# ================= CART SECTION =================
st.header("🛒 Cart Summary")

total = 0

for item in st.session_state.cart:
    total += item["total_price"]

if total > 0:

    pdf_file = generate_pdf(st.session_state.cart, total)

    if st.button("📄 Download PDF & Send Order to Email"):

        success = send_order_email(st.session_state.cart, total, pdf_file)

        if success:
            st.success("✅ Order Sent to Email Successfully!")

    st.download_button(
        label="⬇ Download Only PDF",
        data=pdf_file,
        file_name="order_summary.pdf",
        mime="application/pdf",
    )

    st.subheader(f"💰 Final Amount: ₹{total}")
    st.write("🚚 Delivery Charges Not Included")

    # Clear cart button
    if st.button("✅ Clear Cart After Order"):
        st.session_state.cart = []
        local_storage.deleteItem("cart")
        st.success("Cart Cleared Successfully 🎉")

else:
    st.info("Your cart is empty.")
