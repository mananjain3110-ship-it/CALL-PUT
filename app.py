import streamlit as st
import pandas as pd
from nsepython import nse_optionchain_scrapper, nse_quote_ltp

# --- SETUP & SESSION ---
st.set_page_config(page_title="Nifty Trading Terminal", layout="wide")

if 'balance' not in st.session_state:
    st.session_state.balance = 100000.0
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FETCH DATA ---
@st.cache_data(ttl=30)
def fetch_data():
    try:
        data = nse_optionchain_scrapper("NIFTY")
        ltp = nse_quote_ltp("NIFTY")
        return data['records']['data'], data['records']['expiryDates'], ltp
    except:
        return [], [], 0

records, expiries, nifty_spot = fetch_data()

# --- TOP NAVIGATION ---
st.title("⚡ Nifty Live Option Terminal")
c1, c2, c3 = st.columns([1, 1, 2])
selected_expiry = c1.selectbox("Select Expiry", expiries)
c2.metric("NIFTY 50", nifty_spot)
c3.metric("Available Margin", f"₹{st.session_state.balance:,.2f}")

# --- PROCESS DATA FOR THE GRID ---
# Filter data for the selected expiry and create a side-by-side view
chain_list = []
for r in records:
    if r['expiryDate'] == selected_expiry:
        # Keep strikes near the current spot price for better UI (ATM +/- 500 points)
        if nifty_spot - 500 <= r['strikePrice'] <= nifty_spot + 500:
            chain_list.append({
                "CALL OI": r.get('CE', {}).get('openInterest', 0),
                "CALL LTP": r.get('CE', {}).get('lastPrice', 0),
                "STRIKE": r['strikePrice'],
                "PUT LTP": r.get('PE', {}).get('lastPrice', 0),
                "PUT OI": r.get('PE', {}).get('openInterest', 0),
            })

df_chain = pd.DataFrame(chain_list)

# --- TRADING UI ---
tab1, tab2 = st.tabs(["🔥 Live Option Chain", "💼 My Positions"])

with tab1:
    col_chain, col_order = st.columns([3, 1])
    
    with col_chain:
        st.subheader(f"Option Chain: {selected_expiry}")
        # Highlighting the Strike Price column
        st.dataframe(
            df_chain.style.background_gradient(subset=['CALL OI', 'PUT OI'], cmap='Blues')
            .highlight_max(subset=['STRIKE'], color='lightgrey'),
            use_container_width=True, height=500
        )
        
    with col_order:
        st.subheader("Place Trade")
        with st.form("trade_form"):
            side = st.radio("Side", ["CALL", "PUT"], horizontal=True)
            strike = st.selectbox("Select Strike", df_chain['STRIKE'].tolist())
            lots = st.number_input("Lots (1 Lot = 50)", min_value=1, value=1)
            
            # Find current price for the form selection
            row = df_chain[df_chain['STRIKE'] == strike].iloc[0]
            exec_price = row['CALL LTP'] if side == "CALL" else row['PUT LTP']
            
            st.info(f"Execution Price: ₹{exec_price}")
            
            if st.form_submit_button("BUY NOW", use_container_width=True, type="primary"):
                total_cost = exec_price * lots * 50
                if st.session_state.balance >= total_cost:
                    st.session_state.balance -= total_cost
                    st.session_state.portfolio.append({
                        "Instrument
