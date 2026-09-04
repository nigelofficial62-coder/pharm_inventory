import streamlit as st

st.set_page_config(layout="wide", page_title="Sentinel | OPAS")

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
        font-size: 3rem;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    .sentinel-subtitle {
        color: #475569;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='sentinel-title'>SENTINEL</div>", unsafe_allow_html=True)
st.markdown("<div class='sentinel-subtitle'>Outpatient Pharmacy Automation System (OPAS) Command Center</div>", unsafe_allow_html=True)

st.markdown("### Welcome to Sentinel.")
st.markdown("Please select a machine module from the sidebar on the left to begin.")

st.info("Navigation: Use the sidebar to toggle between iPTL Shelves and the ROWA Machine.")
