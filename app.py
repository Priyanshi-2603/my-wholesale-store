import streamlit as st
import json
import urllib.parse
from streamlit_local_storage import LocalStorage
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

# ---------------- SESSION PAGE CONTROL ----------------
if "page" not in st.session_state:
    st.session_state.page = "shop"

# ---------------- LOAD PRODUCTS ----------------
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

local_storage = LocalStorage()

# ---------------- LOAD CART ----------------
if "cart" not in st.session_state:
    saved_cart = local_storage.getItem("cart")
    st.session_state.cart = json.loads(saved_cart) if saved_cart else []

# ---------------- PRODUCT ADD SUCCESS TRACKER ----------------
if "added_product" not in st.session_state:
    st.session_state.added_product = None


# ---------------- ADD TO CART ----------------
def add_to_cart(product_id, product_name, size, price, dozens, image):

    # Remove same product+size first
    st.session_state.cart = [
        item
        for item in st.session_state.cart
        if not (item["product"] == product_name and item["size"] == size)
    ]

    item = {
        "product": product_name,
        "size": size,
        "dozens": dozens,
        "quantity": dozens * 12,
        "total_price": price * 12 * dozens,
        "image": image,
    }

    st.session_state.cart.append(item)
    local_storage.setItem("cart", json.dumps(st.session_state.cart))

    # Store which product was added
    st.session_state.added_product = product_id


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
    total = sum(item["total_price"] for item in st.session_state.cart)

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
                st.session_state.cart = []
                local_storage.deleteItem("cart")
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
                    st.image(p["image"], use_container_width="True")

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

                    st.write(f"Total Price: ₹{price * 12 * dozens}")

                    if st.button("Add to Cart", key=f"add_{p['id']}_{idx}"):
                        add_to_cart(p["id"], p["name"], size, price, dozens, p["image"])
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

        total = sum(item["total_price"] for item in st.session_state.cart)

        st.markdown(
            f"""
            <div class="sticky-cart">
                <a href="?page=checkout">
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


# ============================================================
# ================= CHECKOUT PAGE ============================
# ============================================================

if st.session_state.page == "checkout":

    st.title("🧾 Checkout Page")

    if st.button("⬅ Back to Shop"):
        st.session_state.page = "shop"
        st.rerun()

    st.markdown("---")

    customer_name = st.text_input("Customer Name")
    customer_whatsapp = st.text_input("Customer WhatsApp Number")

    total = sum(item["total_price"] for item in st.session_state.cart)
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
                local_storage.deleteItem("cart")
