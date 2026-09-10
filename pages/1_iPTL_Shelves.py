import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide", page_title="SENTINEL")

# --- ENTERPRISE CSS ---
st.markdown("""
<style>
    /* Clean off-white background to create depth for the white shelves */
    .stApp {
        background-color: #f8fafc; 
    }
    
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
    
    /* Sleek typography */
    .sentinel-title { 
        color: #097C87; 
        font-weight: 900; 
        font-family: 'Inter', sans-serif; 
        font-size: 2.5rem;
        letter-spacing: -0.02em;
        margin-bottom: 1rem;
    }
    
    .shelf-container {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 4px;
        background-color: #ffffff;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 24px;
        box-shadow: 0 2px 10px rgba(9, 124, 135, 0.06);
        border: 1px solid #e2e8f0;
    }
    
    .bin-box {
        padding: 2px;
        border-radius: 3px;
        text-align: center;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #1e293b;
    }
    .bin-box:hover { transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10; }
    
    .span-1 { grid-column: span 1; }
    .span-2 { grid-column: span 2; }
    
    /* Custom Color Palette based on Health % */
    .status-green { background-color: #A1CCA6; }     /* >66% */
    .status-yellow { background-color: #F9D779; }    /* 33-66% */
    .status-red { background-color: #FCA47C; }       /* <33% */
    .status-overflow { background-color: #64748b; color: #ffffff; border: 1px solid #475569; }
    .status-grey { background-color: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; box-shadow: none; }
    
    .tabletop {
        grid-column: span 8;
        height: 4px;
        background-color: #097C87; 
        margin: 6px 0;
        border-radius: 2px;
        opacity: 0.85;
    }
    .shelf-title { 
        text-align: center; 
        color: #097C87; 
        margin-bottom: 10px; 
        font-weight: 800; 
        font-size: 1.0rem; 
        text-transform: uppercase; 
        letter-spacing: 0.05em; 
    }
    
    div[data-testid="stPopover"] > button, div.stButton > button {
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        background-color: #ffffff;
        color: #475569;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div[data-testid="stPopover"] > button:hover, div.stButton > button:hover {
        border-color: #097C87;
        color: #097C87;
    }
</style>
""", unsafe_allow_html=True)

# --- SHELF CONFIGURATIONS ---
shelf_configs = {
    "Shelf 1": ["8", "8", "(2,1,1,2)", "4", "TABLE", "(2,1,1,2)", "8", "(2,1,2,2)"],
    "Shelf 2": ["8", "8", "4", "4", "TABLE", "4", "(2,1,1,2)", "8"],
    "Shelf 3": ["8", "8", "(1,1,1,2)", "(1,1,2,2)", "TABLE", "(1,1,2,2)", "8", "(1,2,2,2)"],
    "Shelf 4": ["8", "8", "(1,1,1,2)", "(1,1,2,2)", "TABLE", "4", "8", "(1,2,1,1)"],
    "Shelf 5": ["8", "8", "(2,1,1,2)", "4", "TABLE", "(2,1,1,2)", "8", "(2,1,2,2)"],
    "Shelf 6": ["8", "8", "4", "4", "TABLE", "4", "4", "4"],
    "Shelf 7": ["8", "8", "(1,1,1,2)", "(2,1,1,2)", "TABLE", "4", "(2,1,1,2)", "(2,1,1,2)"],
    "Shelf 8": ["8", "8", "(1,1,2,1)", "(1,1,2,2)", "TABLE", "4", "8", "(2,1,1,1)"]
}

def parse_layer(layer_str):
    if pd.isna(layer_str): return []
    layer_str = str(layer_str).strip()
    if layer_str == "TABLE": return []
    elif layer_str == "8": return [1] * 8
    elif layer_str == "4": return [2] * 4
    elif layer_str.startswith("("):
        nums = layer_str.strip("()").replace(" ", "").split(",")
        widths = []
        for n in nums:
            if n == "2": widths.extend([1, 1])
            elif n == "1": widths.append(2)
        return widths
    return []

# --- APP LAYOUT ---
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.markdown("<div class='sentinel-title'>iPTL SHELVES</div>", unsafe_allow_html=True)
with header_col2:
    st.write("") 
    if 'iptl_data' not in st.session_state:
        with st.popover("⚙️ Manage Data", use_container_width=True):
            st.caption("Corporate network blocking uploads? Use the Paste tab.")
            tab_up, tab_paste = st.tabs(["Upload File", "Paste CSV Text"])
            
            with tab_up:
                uploaded_file = st.file_uploader("Upload iPTL SSRS Report", type=["csv"])
                if uploaded_file and st.session_state.get('iptl_uploaded_name') != uploaded_file.name:
                    content = uploaded_file.getvalue().decode('utf-8')
                    lines = content.split('\n')
                    skip_idx = 0
                    for i, line in enumerate(lines[:15]):
                        if 'ARTICLE' in line.upper() or 'BALANCE' in line.upper() or 'TEXTBOX36' in line.upper():
                            skip_idx = i
                            break
                    ssrs_df = pd.read_csv(io.StringIO(content), skiprows=skip_idx)
                    
                    # Clean and standardize columns (handles ARTICLE_NAME1, TOTAL_BALANCE, etc.)
                    ssrs_df.columns = [str(c).upper().replace('_', ' ').replace('1', '').strip() for c in ssrs_df.columns]
                    col_mapping = {}
                    for c in ssrs_df.columns:
                        if c in ['ARTICLE NAME', 'ITEM NAME'] and 'Medication' not in col_mapping.values(): 
                            col_mapping[c] = 'Medication'
                        if c in ['TOTAL BALANCE', 'BALANCE QTY', 'TEXTBOX36'] and 'Current_Stock' not in col_mapping.values(): 
                            col_mapping[c] = 'Current_Stock'
                    ssrs_df = ssrs_df.rename(columns=col_mapping)
                    ssrs_df = ssrs_df.loc[:, ~ssrs_df.columns.duplicated()]
                    
                    if 'Medication' in ssrs_df.columns:
                        ssrs_df = ssrs_df.dropna(subset=['Medication'])
                        ssrs_df = ssrs_df.drop_duplicates(subset=['Medication'])
                        st.session_state['iptl_data'] = ssrs_df
                        st.session_state['iptl_uploaded_name'] = uploaded_file.name
                        st.rerun()
                    else:
                        st.error("Could not find an 'ARTICLE NAME' or 'ITEM NAME' column in the uploaded file.")
                    
            with tab_paste:
                pasted_text = st.text_area("Paste raw CSV content here:", height=150)
                if st.button("Process Pasted Data", use_container_width=True) and pasted_text:
                    try:
                        lines = pasted_text.split('\n')
                        skip_idx = 0
                        for i, line in enumerate(lines[:15]):
                            if 'ARTICLE' in line.upper() or 'BALANCE' in line.upper() or 'TEXTBOX36' in line.upper():
                                skip_idx = i
                                break
                        # Use sep=None, engine='python' to automatically detect if pasted from Excel (Tabs) or Notepad (Commas)
                        ssrs_df = pd.read_csv(io.StringIO(pasted_text), skiprows=skip_idx, sep=None, engine='python')
                        
                        # Clean and standardize columns
                        ssrs_df.columns = [str(c).upper().replace('_', ' ').replace('1', '').strip() for c in ssrs_df.columns]
                        col_mapping = {}
                        for c in ssrs_df.columns:
                            if c in ['ARTICLE NAME', 'ITEM NAME'] and 'Medication' not in col_mapping.values(): 
                                col_mapping[c] = 'Medication'
                            if c in ['TOTAL BALANCE', 'BALANCE QTY', 'TEXTBOX36'] and 'Current_Stock' not in col_mapping.values(): 
                                col_mapping[c] = 'Current_Stock'
                        ssrs_df = ssrs_df.rename(columns=col_mapping)
                        ssrs_df = ssrs_df.loc[:, ~ssrs_df.columns.duplicated()]
                        
                        if 'Medication' not in ssrs_df.columns:
                            raise KeyError("The column 'ARTICLE NAME' was not found. Please ensure you copied the column headers!")
                            
                        ssrs_df = ssrs_df.dropna(subset=['Medication'])
                        ssrs_df = ssrs_df.drop_duplicates(subset=['Medication'])
                        st.session_state['iptl_data'] = ssrs_df
                        st.session_state['iptl_uploaded_name'] = "pasted_data"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to parse pasted data: {e}")
    else:
        if st.button("🔄 Upload New Data", use_container_width=True):
            del st.session_state['iptl_data']
            if 'iptl_uploaded_name' in st.session_state:
                del st.session_state['iptl_uploaded_name']
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

df = None
if 'iptl_data' in st.session_state:
    ssrs_df = st.session_state['iptl_data']
    try:
        raw_master = pd.read_csv("master_config.csv")
        
        # Process the master config to handle Primary and Overflow bins
        records = []
        for _, row in raw_master.iterrows():
            shelf_str = 'Shelf ' + str(row['Shelf']).strip()
            bin_str = str(row['Bin']).strip()
            bins = [b.strip() for b in bin_str.split('/') if b.strip()]
            for i, b in enumerate(bins):
                new_row = row.copy()
                new_row['Shelf'] = shelf_str
                new_row['Bin'] = f"Bin {b}"
                new_row['Is_Overflow'] = (i > 0)
                new_row['Primary_Bin'] = f"Bin {bins[0]}"
                records.append(new_row)
                
        master_df = pd.DataFrame(records)
        df = pd.merge(master_df, ssrs_df[['Medication', 'Current_Stock']], on='Medication', how='left')
        df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0).astype(int)
        
        if 'P95_DAILY_DEMAND' in df.columns:
            df['Target_Level'] = pd.to_numeric(df['P95_DAILY_DEMAND'], errors='coerce')
        elif '3_Day_Consumption' in df.columns:
            df['Target_Level'] = pd.to_numeric(df['3_Day_Consumption'], errors='coerce')
        elif 'Max_Capacity' in df.columns:
            df['Target_Level'] = pd.to_numeric(df['Max_Capacity'], errors='coerce')
        else:
            df['Target_Level'] = pd.Series(100, index=df.index)
            
        if 'VELOCITY_CATEGORY' in df.columns:
            df['Type'] = df['VELOCITY_CATEGORY']
            
        df['Target_Level'] = df['Target_Level'].fillna(100)
        df['Health_Pct'] = df['Current_Stock'] / df['Target_Level']
        
        def calculate_status(row):
            if pd.isna(row.get('Type')): return 'grey'
            if row.get('Is_Overflow', False): return 'overflow'
            pct = row['Health_Pct']
            if pct >= 1.0: return 'green'
            elif pct >= 0.5: return 'yellow'
            else: return 'red'
                
        df['Status'] = df.apply(calculate_status, axis=1)
        
        healthy_bins = len(df[df['Status'] == 'green'])
        warning_bins = len(df[df['Status'] == 'yellow'])
        critical_bins = len(df[df['Status'] == 'red'])
        
        st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }
        .metric-title {
            color: #64748b; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 4px solid #A1CCA6;">
                <div class="metric-title">Healthy (≥100%)</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #A1CCA6;">{healthy_bins}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 4px solid #F9D779;">
                <div class="metric-title">Warning (50-100%)</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #d4a82c;">{warning_bins}</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 4px solid #FCA47C;">
                <div class="metric-title">Critical (<50%)</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #FCA47C;">{critical_bins}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error("master_config.csv not found.")
else:
    st.info("Awaiting Data. Please use the Manage Data menu above to upload an SSRS report to activate the shelves.")

# --- TABS ---
tab1, tab2 = st.tabs(["iPTL Shelves Overview", "iPTL Restock Action List"])

with tab1:
    shelves_list = [f"Shelf {i}" for i in range(1, 9)]
    
    for i in range(0, len(shelves_list), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(shelves_list):
                shelf_name = shelves_list[i+j]
                with cols[j]:
                    st.markdown(f"<div class='shelf-title'>{shelf_name}</div>", unsafe_allow_html=True)
                    
                    html_grid = "<div class='shelf-container'>"
                    bin_counter = 1
                    
                    for layer_str in shelf_configs[shelf_name]:
                        if layer_str == "TABLE":
                            html_grid += "<div class='tabletop' title='Tabletop Divider'></div>"
                            continue
                            
                        widths = parse_layer(layer_str)
                        for w in widths:
                            bin_id = f"Bin {bin_counter}"
                            span_class = "span-2" if w == 2 else "span-1"
                            
                            if df is not None:
                                row = df[(df['Shelf'] == shelf_name) & (df['Bin'] == bin_id)]
                                if not row.empty:
                                    status = row.iloc[0]['Status'].lower()
                                    med = row.iloc[0]['Medication']
                                    
                                    if status == 'overflow':
                                        primary = row.iloc[0]['Primary_Bin']
                                        tooltip = f"OVERFLOW&#10;Primary: {primary}&#10;{med}"
                                    else:
                                        stock = int(row.iloc[0]['Current_Stock'])
                                        target = int(row.iloc[0]['Target_Level'])
                                        pct = int(row.iloc[0]['Health_Pct'] * 100)
                                        tooltip = f"{med}&#10;Stock: {stock} / {target} ({pct}%)"
                                else:
                                    status = "grey"
                                    tooltip = f"Empty ({bin_id})"
                            else:
                                status = "grey"
                                tooltip = f"{shelf_name} - {bin_id}"
                                
                            html_grid += f"<div class='bin-box status-{status} {span_class}' title='{tooltip}'>{bin_counter}</div>"
                            bin_counter += 1
                            
                    html_grid += "</div>"
                    st.markdown(html_grid, unsafe_allow_html=True)

with tab2:
    if df is not None:
        st.markdown("<h3 style='color:#097C87;'>Restock Action List</h3>", unsafe_allow_html=True)
        
        # Velocity Toggle
        vel_filter = st.radio("Filter by Velocity Category:", ["All", "Fast-Moving", "Medium-Moving", "Slow-Moving"], horizontal=True)
        
        action_df = df[df['Status'].isin(['yellow', 'red'])].copy()
        
        if vel_filter != "All":
            action_df = action_df[action_df['Type'] == vel_filter]
            
        action_df = action_df.sort_values(by='Health_Pct', ascending=True)
            
        # Display the formatted dataframe
        display_df = action_df[['Shelf', 'Bin', 'Medication', 'Current_Stock', 'Target_Level', 'Type', 'Health_Pct']]
        display_df = display_df.rename(columns={'Target_Level': 'P95_Daily_Demand', 'Type': 'Velocity_Category', 'Health_Pct': 'Health %'})
        
        def color_health(val):
            if val < 0.5:
                return 'background-color: #FCA47C; color: #1e293b'
            elif val < 1.0:
                return 'background-color: #F9D779; color: #1e293b'
            else:
                return 'background-color: #A1CCA6; color: #1e293b'
                
        styled_df = display_df.style.format({'Health %': '{:.1%}'}).map(color_health, subset=['Health %'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("Awaiting data upload.")
