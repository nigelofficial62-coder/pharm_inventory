import streamlit as st
from supabase import create_client, Client, ClientOptions
import httpx
import pandas as pd
import datetime
import time

@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["supabase"]["url"]
    key: str = st.secrets["supabase"]["key"]
    
    # Configure custom httpx client with generous timeouts
    # Default httpx timeout is 5.0s, which causes httpx.ReadTimeout on slow queries or cloud latency
    # Connect timeout: 10s, Read/Write timeout: 30s
    timeout_config = httpx.Timeout(30.0, connect=10.0)
    
    # Force bypass SSL verification (Fixes CERTIFICATE_VERIFY_FAILED on local laptops with strict antivirus/firewalls)
    custom_client = httpx.Client(verify=False, timeout=timeout_config)
    
    return create_client(
        url, 
        key, 
        options=ClientOptions(
            httpx_client=custom_client,
            postgrest_client_timeout=30
        )
    )

def execute_with_retry(query_fn, retries: int = 2, delay: float = 1.0):
    """
    Executes a Supabase query builder with retries on transient network/timeout errors.
    """
    last_err = None
    for attempt in range(retries + 1):
        try:
            return query_fn().execute()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay * (attempt + 1))
            else:
                raise last_err

def fetch_latest_inventory(system_type: str):
    """
    Fetches the most recent snapshot for a given system type.
    Returns: (df, timestamp_string) or (None, None)
    """
    supabase = init_supabase()
    
    # First, find the most recent created_at timestamp
    response = execute_with_retry(
        lambda: supabase.table(f"{system_type.lower()}_inventory_snapshots")
                       .select("created_at")
                       .order("created_at", desc=True)
                       .limit(1)
    )
    
    if not response.data:
        return None, None
        
    latest_time = response.data[0]['created_at']
    
    # Fetch all rows that share that exact timestamp
    data_response = execute_with_retry(
        lambda: supabase.table(f"{system_type.lower()}_inventory_snapshots")
                       .select("*")
                       .eq("created_at", latest_time)
    )
    
    if not data_response.data:
        return None, None
        
    df = pd.DataFrame(data_response.data)
    # Map back to original dataframe column names so the app doesn't break
    df = df.rename(columns={
        "medication_name": "Medication",
        "current_stock": "Current_Stock",
        "target_level": "Target_Level",
        "health_pct": "Health_Pct"
    })
    
    return df, latest_time

@st.cache_data(ttl=15, show_spinner=False)
def fetch_active_overrides(system_type: str, since_timestamp: str) -> dict:
    """
    Fetches actions and computes the active overrides.
    - OUT_OF_STOCK permanently stays active until manually reset or restocked.
    - RESTOCKED only stays active if it occurred AFTER the last inventory upload.
    Cached for 15s to keep UI snappy (0ms latency on bin clicks),
    while automatically clearing on actions and syncing across clients.
    """
    supabase = init_supabase()
    
    # Only select needed columns to minimize data transfer over network
    response = execute_with_retry(
        lambda: supabase.table(f"{system_type.lower()}_restock_actions")
                       .select("shelf_bin_id, action_type, created_at")
                       .order("created_at", desc=False)
    )
    
    overrides = {}
    if response.data:
        for row in response.data:
            act = row.get("action_type")
            bin_id = row.get("shelf_bin_id")
            action_time = row.get("created_at")
            
            if act == "OUT_OF_STOCK":
                overrides[bin_id] = "purple"
            elif act == "RESTOCKED":
                # Restocks vanish if a new inventory CSV was uploaded AFTER the restock happened
                if since_timestamp and action_time >= since_timestamp:
                    overrides[bin_id] = "blue"
                else:
                    if bin_id in overrides:
                        del overrides[bin_id]
            elif act == "RESET":
                if bin_id in overrides:
                    del overrides[bin_id]
                    
    return overrides

def save_inventory_snapshot(df: pd.DataFrame, system_type: str) -> str:
    """
    Saves the entire dataframe to the snapshot table.
    Returns the created_at timestamp string.
    """
    supabase = init_supabase()
    records = []
    sg_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(sg_tz).isoformat()
    
    for _, row in df.iterrows():
        records.append({
            "created_at": now,
            "system_type": system_type,
            "medication_name": str(row.get("Medication", "")),
            "current_stock": int(row.get("Current_Stock", 0)),
            "target_level": int(row.get("Target_Level", 100)),
            "health_pct": float(row.get("Health_Pct", 1.0))
        })
        
    # Supabase supports bulk inserts - batch in chunks of 500
    if records:
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            execute_with_retry(
                lambda c=chunk: supabase.table(f"{system_type.lower()}_inventory_snapshots").insert(c)
            )
        
    # Invalidate cached overrides since snapshot timestamp changed
    fetch_active_overrides.clear()
    return now

def log_bin_action(system_type: str, med_name: str, shelf_bin_id: str, health_pct: float, action_type: str):
    """
    Logs an action (RESTOCKED, OUT_OF_STOCK)
    """
    supabase = init_supabase()
    sg_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(sg_tz).isoformat()
    
    execute_with_retry(
        lambda: supabase.table(f"{system_type.lower()}_restock_actions").insert({
            "created_at": now,
            "system_type": system_type,
            "medication_name": med_name,
            "shelf_bin_id": shelf_bin_id,
            "health_at_time_of_restock": float(health_pct) if health_pct is not None else 0.0,
            "action_type": action_type
        })
    )
    # Clear cache so UI reflects change immediately
    fetch_active_overrides.clear()

def remove_bin_action(system_type: str, med_name: str, shelf_bin_id: str, health_pct: float):
    """
    Logs a RESET action. We log this instead of deleting rows so your ML dataset keeps a full history
    of human corrections (e.g. they clicked Restock, realized it was a mistake, and clicked Reset).
    """
    log_bin_action(system_type, med_name, shelf_bin_id, health_pct, "RESET")
