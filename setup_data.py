import pandas as pd
import random
import os

def setup_files():
    # 1. Create the Master Config File (Static settings)
    data = []
    meds = ["Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 250mg", "Lisinopril 10mg", 
            "Metformin 500mg", "Atorvastatin 20mg", "Amlodipine 5mg", "Omeprazole 20mg", 
            "Losartan 50mg", "Simvastatin 10mg", "Aspirin 81mg", "Gabapentin 300mg",
            "Specialty Med A", "Specialty Med B", "Slow Mover C", "Slow Mover D"]

    for shelf in range(1, 9):
        for bin_id in range(1, 61):
            med = random.choice(meds)
            
            if "Specialty" in med or "Slow Mover" in med:
                item_type = "Slow-Moving"
                max_cap = random.randint(20, 50)
                reorder_threshold = int(max_cap * 0.3)
                topup_threshold = 0
            else:
                item_type = "Fast-Moving"
                max_cap = random.randint(100, 300)
                reorder_threshold = 0 
                topup_threshold = int(max_cap * 0.4)
            
            data.append({
                "Shelf": f"Shelf {shelf}",
                "Bin": f"Bin {bin_id}",
                "Medication": med,
                "Type": item_type,
                "Max_Capacity": max_cap,
                "Reorder_Threshold": reorder_threshold,
                "TopUp_Threshold": topup_threshold
            })

    master_df = pd.DataFrame(data)
    master_df.to_csv("master_config.csv", index=False)
    print("Created master_config.csv (Your PAR levels and mapping)")

    # 2. Create the Mock SSRS Export (Only contains fluctuating balances)
    ssrs_data = []
    for _, row in master_df.iterrows():
        ssrs_data.append({
            "Shelf": row['Shelf'],
            "Bin": row['Bin'],
            "Medication": row['Medication'],
            "Current_Stock": random.randint(0, int(row['Max_Capacity']))
        })
    
    ssrs_df = pd.DataFrame(ssrs_data)
    ssrs_df.to_csv("mock_ssrs_inventory.csv", index=False)
    print("Created mock_ssrs_inventory.csv (Mimics your actual raw export)")

if __name__ == "__main__":
    setup_files()
