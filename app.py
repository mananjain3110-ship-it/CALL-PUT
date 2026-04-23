import streamlit as st
import pandas as pd
from nsepython import nse_optionchain_scrapper, nse_quote_ltp
import datetime

# --- CONFIG & STATE ---
st.set_page_config(page_title="Nifty Live Simulator", layout="wide")

if 'balance' not in st.session_state:
    st.session_state.balance = 100000.0
if 'positions' not in st.session_state:
    st.session_state.positions = []

# CSS to inject for the "Sticky" Toolbar
st.markdown("""
    <style>
    .stAppHeader {
        background-color: #f0f2f6;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.trading-toolbar) {
        position: sticky;
        top: 2.8rem;
        z-index: 999;
        background: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LIVE DATA FETCH ---
def get_data():
    try:
        # Fetching Nifty 50 Spot
        ltp = nse_quote_ltp("NIFTY")
        data = nse_optionchain_scrapper("NIFTY")
        return ltp, data['records']['data'], data['records']['expiryDates']
    except:
        return 19500, [], [] # Fallback values

ltp, records, expiries = get_data()

# --- TOP TRADING TOOLBAR ---
with st.container():
    st.markdown('<div class="trading-toolbar">', unsafe_allow_html=True)
    cols = st.columns([1.5, 1.5, 1, 1, 1, 1.5])
    
    with cols[0]:
        strike_select = st.selectbox("Strike", [r['strikePrice'] for r in records if r['strikePrice'] % 100 == 0], index=10)
    with cols[1]:
        expiry_select = st.selectbox("Expiry", expiries)
    with cols[2]:
        opt_type = st.radio("Type", ["CE", "PE"], horizontal=True)
    with cols[3]:
        qty = st.number_input("Qty", value=50, step=50)
    
    # Calculate current price for selected option
    current_price = 0
    for r in records:
        if r['strikePrice'] == strike_select and r['expiryDate'] == expiry_select:
            current_price = r.get(opt_type, {}).get('lastPrice', 0)
    
    with cols[4]:
        st.metric("Premium", f"₹{current_price}")
        
    with cols[5]:
        st.write("") # Spacer
        if st.button("🚀 EXECUTE BUY", use_container_width=True, type="primary"):
            cost = current_price * qty
            if st.session_state.balance >= cost:
                st.session_state.balance -= cost
                st.session_state.positions.append({
                    "Symbol": f"NIFTY {strike_select} {opt_type}",
                    "Qty": qty,
                    "Entry": current_price,
                    "Total": cost
                })
                st.toast(f"Order Executed: {qty} Qty of {strike_select} {opt_type}", icon="✅")
            else:
                st.error("Low Balance!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN DASHBOARD AREA ---
st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 Active Portfolio")
    if st.session_state.positions:
        df = pd.DataFrame(st.session_state.positions)
        st.table(df)
        if st.button("Clear All Positions"):
            st.session_state.positions = []
            st.rerun()
    else:
        st.info("Your portfolio is empty. Use the toolbar above to Add/Buy options.")

with col_right:
    st.subheader("💰 Account Summary")
    st.metric("Available Margin", f"₹{st.session_state.balance:,.2f}")
    st.metric("NIFTY 50", f"{ltp}", delta="Live Spot")
    
    if st.button("Reset Funds"):
        st.session_state.balance = 100000.0
        st.rerun()
