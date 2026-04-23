import streamlit as st
import pandas as pd
from nsepython import nse_optionchain_scrapper, nse_quote_ltp
import datetime

# --- INITIALIZE SIMULATOR STATE ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100000.0  # Starting Virtual Cash: ₹1 Lakh
if 'positions' not in st.session_state:
    st.session_state.positions = []      # Active Trades
if 'history' not in st.session_state:
    st.session_state.history = []        # Closed Trades

st.set_page_config(page_title="Nifty Live Simulator", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=60) # Cache for 1 minute to avoid NSE blocking
def fetch_live_data():
    try:
        data = nse_optionchain_scrapper("NIFTY")
        ltp = nse_quote_ltp("NIFTY")
        return data['records']['data'], ltp, data['records']['expiryDates']
    except:
        return None, None, None

records, ltp, expiry_dates = fetch_live_data()

# --- TOP BAR: PORTFOLIO SUMMARY ---
st.title("💸 Nifty Options Paper Trading Simulator")
c1, c2, c3 = st.columns(3)
c1.metric("Virtual Balance", f"₹{st.session_state.balance:,.2f}")
c2.metric("Active Positions", len(st.session_state.positions))
c3.metric("Nifty Spot", f"₹{ltp}")

# --- TRADING PANEL ---
st.sidebar.header("🕹️ Place a Trade")
if records:
    exp_date = st.sidebar.selectbox("Expiry", expiry_dates)
    strike = st.sidebar.number_input("Strike Price", value=int(round(ltp/50)*50), step=50)
    opt_type = st.sidebar.radio("Option Type", ["CE", "PE"])
    qty = st.sidebar.number_input("Quantity (Lot Size: 50)", min_value=50, step=50)

    # Find the current price for the selected strike
    current_opt_price = 0
    for r in records:
        if r['strikePrice'] == strike and r['expiryDate'] == exp_date:
            current_opt_price = r.get(opt_type, {}).get('lastPrice', 0)

    st.sidebar.write(f"**Current Premium:** ₹{current_opt_price}")
    
    if st.sidebar.button("Execute BUY Order"):
        total_cost = current_opt_price * qty
        if st.session_state.balance >= total_cost:
            st.session_state.balance -= total_cost
            st.session_state.positions.append({
                "strike": strike, "type": opt_type, "qty": qty, 
                "buy_price": current_opt_price, "time": datetime.datetime.now().strftime("%H:%M:%S")
            })
            st.sidebar.success(f"Bought {qty} {opt_type} at ₹{current_opt_price}")
        else:
            st.sidebar.error("Insufficient Balance!")

# --- ACTIVE POSITIONS ---
st.subheader("📁 Open Positions")
if st.session_state.positions:
    pos_df = pd.DataFrame(st.session_state.positions)
    # Calculate Live P&L
    temp_pnl = 0
    for i, pos in enumerate(st.session_state.positions):
        # In a real app, you'd fetch the latest LTP here again for real-time P&L
        st.write(f"**{pos['qty']} Qty** of **{pos['strike']} {pos['type']}** bought at **₹{pos['buy_price']}**")
        if st.button(f"Square Off Position {i+1}"):
            # Simple sell logic at same price for demo (or refetch latest)
            st.session_state.balance += (pos['buy_price'] * pos['qty']) 
            st.session_state.positions.pop(i)
            st.rerun()
else:
    st.info("No active trades. Use the sidebar to place your first order.")

st.divider()
if st.button("Reset Simulator"):
    st.session_state.balance = 100000.0
    st.session_state.positions = []
    st.rerun()
