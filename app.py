import streamlit as st
from kiteconnect import KiteConnect
import pandas as pd
import plotly.graph_objects as go
import time

# 🔐 API Setup
api_key = "YOUR_API_KEY"
access_token = "YOUR_ACCESS_TOKEN"

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# 🎯 Page Config
st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📊 Live Trading Dashboard")

# 📥 Inputs
symbol = st.text_input("Enter Symbol", "RELIANCE")
qty = st.number_input("Quantity", min_value=1, value=10)

# 📊 Get Live Price
def get_price(symbol):
    try:
        data = kite.ltp(f"NSE:{symbol}")
        return data[f"NSE:{symbol}"]["last_price"]
    except:
        return None

# 📈 Get Historical Data
def get_data(symbol):
    try:
        instrument_token = 738561  # Example token (RELIANCE)
        data = kite.historical_data(
            instrument_token,
            from_date="2024-04-01",
            to_date="2024-04-10",
            interval="5minute"
        )
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# 🛑 SL & Target
def calculate_sl_target(price):
    sl = price * 0.98
    target = price * 1.05
    return sl, target

# 💰 Order
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
        st.success(f"{action} Order Placed")
    except Exception as e:
        st.error(str(e))

# 🔄 Auto Refresh
placeholder = st.empty()

while True:
    with placeholder.container():

        col1, col2 = st.columns(2)

        # 📊 Price Section
        with col1:
            price = get_price(symbol)
            if price:
                st.metric("Live Price", price)

                sl, target = calculate_sl_target(price)
                st.write(f"Stop Loss: {sl}")
                st.write(f"Target: {target}")

        # 📈 Chart Section
        with col2:
            df = get_data(symbol)

            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close']
                )])

                fig.update_layout(title="Live Chart", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

        # 💰 Buttons
        col3, col4 = st.columns(2)

        with col3:
            if st.button("BUY"):
                place_order(symbol, qty, "BUY")

        with col4:
            if st.button("SELL"):
                place_order(symbol, qty, "SELL")

    time.sleep(5)
    st.rerun()
