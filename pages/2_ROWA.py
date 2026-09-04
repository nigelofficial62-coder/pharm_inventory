import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(layout="wide", page_title="ROWA | Sentinel")

# --- ENTERPRISE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    
    /* Dark Sidebar Override */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    [data-testid="stSidebarNav"] span {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebarNav"] li a:hover {
        background-color: #1E293B !important;
    }
    
    .sentinel-title { 
        color: #097C87; 
        font-weight: 900; 
        font-family: 'Inter', sans-serif; 
        font-size: 2.5rem;
        letter-spacing: -0.02em;
        margin: 0;
        padding-top: 10px;
    }
    
    /* Target the popover button to look sleek */
    div[data-testid="stPopover"] > button {
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        background-color: #ffffff;
        color: #475569;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #097C87;
        color: #097C87;
    }
    
    /* Style Plotly containers to look like white metric cards */
    [data-testid="stPlotlyChart"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        padding: 15px;
        overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER & DATA INGESTION (Right Justified) ---
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.markdown("<h1 class='sentinel-title'>ROWA</h1>", unsafe_allow_html=True)
with header_col2:
    st.write("") # Vertical alignment spacing
    if 'rowa_data' not in st.session_state:
        with st.popover("⚙️ Manage Data", use_container_width=True):
            uploaded_file = st.file_uploader("Upload ROWA SSRS Report", type=["csv"])
            if uploaded_file and st.session_state.get('rowa_uploaded_name') != uploaded_file.name:
                rowa_df = pd.read_csv(uploaded_file)
                st.session_state['rowa_data'] = rowa_df
                st.session_state['rowa_uploaded_name'] = uploaded_file.name
                st.rerun()
    else:
        if st.button("🔄 Upload New Data", use_container_width=True):
            del st.session_state['rowa_data']
            if 'rowa_uploaded_name' in st.session_state:
                del st.session_state['rowa_uploaded_name']
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if 'rowa_data' in st.session_state:
    try:
        master_df = pd.read_csv('rowa_master_config.csv')
    except FileNotFoundError:
        st.error("rowa_master_config.csv is missing. Please ensure the master configuration file is in the root directory.")
        st.stop()
        
    master_df['ITEM_CODE'] = master_df['ITEM_CODE'].astype(str).str.strip()
    
    ssrs_df = st.session_state['rowa_data'].copy()
    ssrs_df['ITEM_CODE1'] = ssrs_df['ITEM_CODE1'].astype(str).str.strip()
    
    # 1. Parse Expiry Dates & Deduplicate SSRS
    ssrs_df['EXPIRY_DT1'] = pd.to_datetime(ssrs_df['EXPIRY_DT1'], format='%d/%m/%Y', errors='coerce')
    ssrs_df = ssrs_df.sort_values(by='EXPIRY_DT1')
    ssrs_dedup = ssrs_df.drop_duplicates(subset=['ITEM_CODE1'], keep='first')
    
    # Merge onto Master Config to retain items with 0 stock
    df = pd.merge(master_df, ssrs_dedup, left_on='ITEM_CODE', right_on='ITEM_CODE1', how='left')
    
    # 2. Map Required Metrics (Converted to int)
    df['Medication'] = df['ITEM_NAME']
    df['Current_Stock'] = pd.to_numeric(df['Textbox36'], errors='coerce').fillna(0).astype(int)
    
    # Max Target is PAR_ALERT_QTY from the master config
    par_col = 'PAR_ALERT_QTY_x' if 'PAR_ALERT_QTY_x' in df.columns else 'PAR_ALERT_QTY'
    df['Max_Target'] = pd.to_numeric(df[par_col], errors='coerce').fillna(0).astype(int)
    
    df['BARCODE'] = df['BARCODE'].fillna('NO')
    
    # Calculate Qty to Load against PAR (Max Target)
    df['Qty_To_Load'] = df['Max_Target'] - df['Current_Stock']
    df['Qty_To_Load'] = df['Qty_To_Load'].apply(lambda x: max(0, int(x)))
    
    # Calculate Health % against PAR (Max Target)
    df['Health %'] = df['Current_Stock'] / df['Max_Target']
    df['Health %'] = df['Health %'].fillna(0)
    
    # 3. Calculate Expiring Soon (< 365 Days)
    today = pd.Timestamp.now()
    df['Days_To_Expiry'] = (df['EXPIRY_DT1'] - today).dt.days
    df['Months_To_Expiry'] = df['Days_To_Expiry'] / 30.44
    
    # Logic for Charts
    def categorize_stock(health):
        if health < 0.33: return "Critical (<33%)"
        elif health <= 0.66: return "Warning (33-66%)"
        elif health <= 1.00: return "Healthy (67-100%)"
        else: return "Overstocked (>100%)"
        
    df['Stock_Status'] = df['Health %'].apply(categorize_stock)
    df['Expiry_Status'] = df.apply(lambda r: "Expiring < 1 Yr" if pd.notnull(r['Days_To_Expiry']) and 0 <= r['Days_To_Expiry'] <= 365 else "Safe Expiry", axis=1)
    
    # Format dates for clean display
    df['Expiry Date'] = df['EXPIRY_DT1'].dt.strftime('%d/%m/%Y').fillna('N/A')
    
    load_df = df[df['Health %'] < 1.0].copy()
    expiring_df = df[df['Expiry_Status'] == "Expiring < 1 Yr"].copy()
    
    # --- METRICS DASHBOARD (Main Page) ---
    stock_counts = df['Stock_Status'].value_counts().to_dict()
    
    bar_data = pd.DataFrame([
        {'Metric': 'Stock Level', 'Status': 'Critical (<33%)', 'Count': stock_counts.get('Critical (<33%)', 0)},
        {'Metric': 'Stock Level', 'Status': 'Warning (33-66%)', 'Count': stock_counts.get('Warning (33-66%)', 0)},
        {'Metric': 'Stock Level', 'Status': 'Healthy (67-100%)', 'Count': stock_counts.get('Healthy (67-100%)', 0)},
        {'Metric': 'Stock Level', 'Status': 'Overstocked (>100%)', 'Count': stock_counts.get('Overstocked (>100%)', 0)},
        {'Metric': 'Expiry', 'Status': 'Expiring < 1 Yr', 'Count': len(expiring_df)},
        {'Metric': 'Expiry', 'Status': 'Safe Expiry', 'Count': len(df) - len(expiring_df)}
    ])
    
    # Filter out 0 counts to keep chart clean
    bar_data = bar_data[bar_data['Count'] > 0]
    
    color_map = {
        'Critical (<33%)': '#FCA47C', 
        'Warning (33-66%)': '#F9D779', 
        'Healthy (67-100%)': '#A1CCA6', 
        'Overstocked (>100%)': '#60A5FA', 
        'Expiring < 1 Yr': '#F9D779', 
        'Safe Expiry': '#A1CCA6'
    }
    
    fig = px.bar(bar_data, y='Metric', x='Count', color='Status', orientation='h', barmode='stack', text='Count',
                 color_discrete_map=color_map)
                 
    fig.update_layout(
        title=dict(text="ROWA SYSTEM OVERVIEW", font=dict(color="#64748b", size=14, family="Inter, sans-serif")),
        xaxis=dict(title="", showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(title="", showgrid=False, tickfont=dict(size=14, color="#475569", family="Inter, sans-serif")),
        showlegend=False,
        bargap=0.45,
        margin=dict(t=40, b=10, l=10, r=10),
        height=160,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    fig.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color='#1e293b', size=16, family="Inter, sans-serif"))
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["ROWA Loading Report", "ROWA Expiry Report", "ROWA Complete Inventory"])
    
    with tab1:
        t1_col1, t1_col2 = st.columns([7, 3])
        with t1_col1:
            st.markdown("<h3 style='color:#097C87; margin-top: 0;'>ROWA Loading Requirements</h3>", unsafe_allow_html=True)
            barcode_filter = st.radio("Filter by Barcode Status:", ["All", "With Barcode (YES)", "Without Barcode (NO)"], horizontal=True)
            
        # Filter based on Barcode Selection
        if barcode_filter == "With Barcode (YES)":
            load_df_filtered = load_df[load_df['BARCODE'] == 'YES'].copy()
        elif barcode_filter == "Without Barcode (NO)":
            load_df_filtered = load_df[load_df['BARCODE'] == 'NO'].copy()
        else:
            load_df_filtered = load_df.copy()
            
        # Calculate Health % against PAR (Max_Target)
        load_df_filtered['Health %'] = load_df_filtered['Current_Stock'] / load_df_filtered['Max_Target']
        load_df_filtered = load_df_filtered.sort_values(by='Health %', ascending=True)
        
        display_load = load_df_filtered[['Medication', 'BARCODE', 'Current_Stock', 'Max_Target', 'Qty_To_Load', 'Health %']]
        display_load = display_load.rename(columns={'Max_Target': 'PAR Target'})
        
        with t1_col2:
            st.write("") # spacing
            csv_export = display_load.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Export Excel",
                data=csv_export,
                file_name=f"ROWA_Pick_List_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
            
        def color_health(val):
            if val < 0.33: return 'background-color: #FCA47C; color: #1e293b'
            elif val <= 0.66: return 'background-color: #F9D779; color: #1e293b'
            else: return 'background-color: #A1CCA6; color: #1e293b'
                
        styled_df = display_load.style.format({'Health %': '{:.1%}'}).map(color_health, subset=['Health %'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=500)

    with tab2:
        st.markdown("<h3 style='color:#097C87; margin-top: 0;'>ROWA Medications Approaching Expiry</h3>", unsafe_allow_html=True)
        display_expiring = expiring_df[['Medication', 'BATCH_NO1', 'Expiry Date', 'Months_To_Expiry', 'Current_Stock']]
        display_expiring = display_expiring.sort_values(by='Months_To_Expiry')
        
        def color_expiry(val):
            if val < 6.0: return 'background-color: #FCA47C; color: #1e293b'
            elif val <= 9.0: return 'background-color: #F9D779; color: #1e293b'
            else: return 'background-color: #A1CCA6; color: #1e293b'
            
        styled_expiring = display_expiring.style.format({'Months_To_Expiry': '{:.1f}'}).map(color_expiry, subset=['Months_To_Expiry'])
        st.dataframe(styled_expiring, use_container_width=True, hide_index=True, height=500)

    with tab3:
        st.markdown("<h3 style='color:#097C87; margin-top: 0;'>ROWA Complete Inventory List</h3>", unsafe_allow_html=True)
        display_all = df[['Medication', 'BARCODE', 'Current_Stock', 'Max_Target', 'Stock_Status', 'Expiry_Status', 'Expiry Date']]
        display_all = display_all.rename(columns={'Max_Target': 'PAR Target'})
        st.dataframe(display_all, use_container_width=True, hide_index=True, height=500)
        
else:
    st.info("Awaiting Data. Please use the Manage Data menu above to upload the ROWA SSRS report.")
