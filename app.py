import streamlit as st
import pandas as pd
from nsepython import nse_optionchain_scrapper, nse_quote_ltp
import plotly.graph_objects as go
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Nifty Option Chain Analyzer", layout="wide")

st.title("📈 Nifty Index Option Chain & Market Trends")

def get_option_chain_data(symbol="NIFTY"):
    # Scrape live data from NSE
    data = nse_optionchain_scrapper(symbol)
    
    # Get Current Market Price (LTP)
    ltp = nse_quote_ltp(symbol)
    
    # Process basic data
    records = data['records']['data']
    expiry_dates = data['records']['expiryDates']
    
    return records, expiry_dates, ltp

try:
    # 1. Sidebar - Configuration
    st.sidebar.header("Settings")
    symbol = st.sidebar.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
    
    # Fetch Data
    records, expiry_dates, ltp = get_option_chain_data(symbol)
    
    selected_expiry = st.sidebar.selectbox("Select Expiry Date", expiry_dates)
    
    # 2. Key Market Indicators
    col1, col2, col3 = st.columns(3)
    
    # Filter data for selected expiry
    filtered_data = [r for r in records if r['expiryDate'] == selected_expiry]
    
    # Calculate PCR (Put-Call Ratio)
    total_ce_oi = sum([r['CE']['openInterest'] for r in filtered_data if 'CE' in r])
    total_pe_oi = sum([r['PE']['openInterest'] for r in filtered_data if 'PE' in r])
    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
    
    col1.metric(f"{symbol} LTP", f"₹{ltp}")
    col2.metric("Put-Call Ratio (OI)", pcr, delta="Bullish" if pcr > 1 else "Bearish")
    col3.metric("Selected Expiry", selected_expiry)

    # 3. Market Trends & Visualization
    st.subheader("Open Interest (OI) Analysis")
    
    # Prepare DataFrame for Plotting
    plot_data = []
    for r in filtered_data:
        strike = r['strikePrice']
        if 'CE' in r:
            plot_data.append({'Strike': strike, 'OI': r['CE']['openInterest'], 'Type': 'Call (CE)', 'Color': 'red'})
        if 'PE' in r:
            plot_data.append({'Strike': strike, 'OI': r['PE']['openInterest'], 'Type': 'Put (PE)', 'Color': 'green'})
            
    df_oi = pd.DataFrame(plot_data)
    
    # Create Bar Chart for OI
    fig_oi = px.bar(df_oi, x='Strike', y='OI', color='Type', 
                   barmode='group', title="Open Interest by Strike Price",
                   color_discrete_map={'Call (CE)': '#EF553B', 'Put (PE)': '#00CC96'})
    
    # Add vertical line for Current Price
    fig_oi.add_vline(x=ltp, line_dash="dash", line_color="blue", annotation_text="At The Money (ATM)")
    
    st.plotly_chart(fig_oi, use_container_width=True)

    # 4. Detailed Option Chain Table
    st.subheader("Live Option Chain Table")
    
    rows = []
    for r in filtered_data:
        row = {
            "Strike": r['strikePrice'],
            "Call_OI": r.get('CE', {}).get('openInterest', 0),
            "Call_LTP": r.get('CE', {}).get('lastPrice', 0),
            "Put_LTP": r.get('PE', {}).get('lastPrice', 0),
            "Put_OI": r.get('PE', {}).get('openInterest', 0),
        }
        rows.append(row)
    
    df_table = pd.DataFrame(rows)
    st.dataframe(df_table.style.background_gradient(subset=['Call_OI', 'Put_OI'], cmap='YlGn'), use_container_width=True)

except Exception as e:
    st.error(f"Error fetching data: {e}. Ensure you have a stable internet connection and NSE website is accessible.")
