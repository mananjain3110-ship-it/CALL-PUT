import streamlit as st
from kiteconnect import KiteConnect

# 🔐 API Setup
api_key = "YOUR_API_KEY"
access_token = "YOUR_ACCESS_TOKEN"

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# 📊 Get Live Price
def get_price(symbol):
    try:
        data = kite.ltp(f"NSE:{symbol}")
        return data[f"NSE:{symbol}"]["last_price"]
    except:
        return None

# 🛑 Risk Management
def calculate_sl_target(price):
    sl = price * 0.98
    target = price * 1.05
    return sl, target

# 💰 Place Order
def place_order(symbol, qty, action):
    try:
        kite.place_order(
            tradingsymbol=symbol,
            exchange="NSE",
            transaction_type=action,
            quantity=qty,
            order_type="MARKET",
            product="MIS"
        )
        return "Success"
    except Exception as e:
        return str(e)

# 🎯 UI
st.title("📊 Trading Dashboard")

symbol = st.text_input("Enter Symbol", "RELIANCE")
qty = st.number_input("Quantity", min_value=1, value=10)

# Get Price
if st.button("Get Price"):
    price = get_price(symbol)
    if price:
        st.success(f"Price: {price}")

        sl, target = calculate_sl_target(price)
        st.info(f"Stop Loss: {sl}")
        st.info(f"Target: {target}")
    else:
        st.error("Error fetching price")

# Buy
if st.button("BUY"):
    result = place_order(symbol, qty, "BUY")
    st.success(result)

# Sell
if st.button("SELL"):
    result = place_order(symbol, qty, "SELL")
    st.success(result)