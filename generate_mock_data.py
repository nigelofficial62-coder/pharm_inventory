import pandas as pd
import random
import os

def generate_mock_data(filename="mock_ssrs_inventory.csv"):
    data = []
    
    # Sample medication names
    meds = ["Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 250mg", "Lisinopril 10mg", 
            "Metformin 500mg", "Atorvastatin 20mg", "Amlodipine 5mg", "Omeprazole 20mg", 
            "Losartan 50mg", "Simvastatin 10mg", "Aspirin 81mg", "Gabapentin 300mg",
            "Specialty Med A", "Specialty Med B", "Slow Mover C", "Slow Mover D"]

    for shelf in range(1, 9): # 8 shelves
        for bin_id in range(1, 61): # 60 bins per shelf
            med = random.choice(meds)
            
            # Determine if it's fast or slow moving based on the name for mock purposes
            if "Specialty" in med or "Slow Mover" in med:
                item_type = "Slow-Moving"
                max_cap = random.randint(20, 50)
                reorder_threshold = int(max_cap * 0.3)
                topup_threshold = 0 # Not used for slow moving
            else:
                item_type = "Fast-Moving"
                max_cap = random.randint(100, 300)
                reorder_threshold = 0 # Not used directly by app due to blind buffer
                topup_threshold = int(max_cap * 0.4)
            
            # Random current stock to simulate green, yellow, and red states
            current = random.randint(0, max_cap)
            
            data.append({
                "Shelf": f"Shelf {shelf}",
                "Bin": f"Bin {bin_id}",
                "Medication": med,
                "Type": item_type,
                "Current_Stock": current,
                "Max_Capacity": max_cap,
                "Reorder_Threshold": reorder_threshold,
                "TopUp_Threshold": topup_threshold
            })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Mock data generated successfully at {os.path.abspath(filename)}")

if __name__ == "__main__":
    generate_mock_data()
