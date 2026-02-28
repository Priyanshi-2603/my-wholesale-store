import streamlit as st
import json
import urllib.parse
from streamlit_local_storage import LocalStorage
import io
import requests
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Shri Girraj Mukut Shringar Kendra Mathura", layout="wide"
)

# ---------------- LOAD PRODUCTS ----------------
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------- LOCAL STORAGE ----------------
local_storage = LocalStorage()

if "cart" not in st.session_state:
    saved_cart = local_storage.getItem("cart")
    st.session_state.cart = json.loads(saved_cart) if saved_cart else []


# ---------------- ADD TO CART ----------------
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
    local_storage.setItem("cart", json.dumps(st.session_state.cart))


# ---------------- UI ----------------
st.title("🛍 Shri Girraj Mukut Shringar Kendra Product Catalogue")

category = st.selectbox("Select Category", list(data.keys()))
subcategory_list = list(data[category].keys())
subcategory_options = ["All"] + subcategory_list
subcategory = st.selectbox("Select Subcategory", subcategory_options)

if subcategory == "All":
    products_by_sub = {k: v for k, v in data[category].items()}
else:
    products_by_sub = {subcategory: data[category].get(subcategory, [])}

search = st.text_input("🔍 Search Product Name")

for sub_name, products in products_by_sub.items():

    cols = st.columns(2)
    idx = 0

    for p in products:

        if search and search.lower() not in p.get("name", "").lower():
            continue

        with cols[idx % 2]:

            st.markdown(f"### {p.get('name','Unnamed')}")

            img_url = p.get("image", "")
            if img_url:
                st.image(img_url, width="stretch")

            prices = p.get("prices", {})
            if prices:

                unique_key = f"{category}_{sub_name}_{p['id']}"

                size = st.selectbox(
                    "Select Size",
                    list(prices.keys()),
                    key=f"size_{unique_key}",
                )

                price = prices[size]

                dozens = st.number_input(
                    "Select Quantity (in dozens)",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"dozen_{unique_key}",
                )

                if st.button("Add to Cart", key=f"btn_{unique_key}"):
                    add_to_cart(p["name"], size, price, dozens, img_url)
                    st.success("Added to cart ✅")

        idx += 1


# ---------------- PDF GENERATION ----------------
def generate_pdf(cart_items, total_amount, name, whatsapp):

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

        elements.append(Paragraph(f"Product: {item['product']}", styles["Normal"]))
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

    elements.append(Paragraph(f"Final Amount: ₹{total_amount}", styles["Heading2"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------- EMAIL FUNCTION ----------------
def send_order_email(cart_items, total_amount, pdf_buffer, name, whatsapp):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = st.secrets["BREVO_API_KEY"]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    html_content = f"""
    <h2>New Order Received</h2>
    <p><b>Name:</b> {name}</p>
    <p><b>WhatsApp:</b> {whatsapp}</p>
    <hr>
    """

    for item in cart_items:
        html_content += f"""
        <div>
            <img src="{item['image']}" width="120"><br>
            <b>{item['product']}</b><br>
            Size: {item['size']}<br>
            Qty: {item['dozens']} dozen ({item['quantity']} pcs)<br>
            Total: ₹{item['total_price']}<br><br>
        </div>
        """

    html_content += f"<h3>Final Amount: ₹{total_amount}</h3>"

    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": st.secrets["RECEIVER_EMAIL"]}],
        sender={"email": st.secrets["SENDER_EMAIL"]},
        subject="New Order Received",
        html_content=html_content,
        attachment=[{"content": pdf_base64, "name": "order_summary.pdf"}],
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        return True
    except ApiException as e:
        st.error(f"Email sending failed: {e}")
        return False


# ---------------- CUSTOMER DETAILS ----------------
st.subheader("🧾 Customer Details")
customer_name = st.text_input("Customer Name")
customer_whatsapp = st.text_input("Customer WhatsApp Number")

# ---------------- CART SECTION ----------------
st.header("🛒 Cart Summary")

total = sum(item["total_price"] for item in st.session_state.cart)

if total > 0:

    if st.button("📄 Place Order"):

        if not customer_name or not customer_whatsapp:
            st.warning("Please enter your name and WhatsApp number.")
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

                st.session_state.cart = []
                local_storage.deleteItem("cart")

                st.success("🎉 Thank you for your order!")
                st.info("We will contact you soon on WhatsApp.")

                # WhatsApp Redirect
                business_number = "917417866405"

                message = f"""
🛍 Order Placed Successfully

Name: {customer_name}
Mobile: {customer_whatsapp}
Total Amount: ₹{total}

Please confirm the order.
"""

                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{business_number}?text={encoded_message}"

                st.markdown(
                    f'<meta http-equiv="refresh" content="2;url={whatsapp_url}">',
                    unsafe_allow_html=True,
                )

    st.subheader(f"💰 Final Amount: ₹{total}")

else:
    st.info("Your cart is empty.")
