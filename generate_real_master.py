import pandas as pd
import random

# We know the shelf configurations. Let's calculate exactly how many bins exist
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
    if layer_str == "8": return [1] * 8
    elif layer_str == "4": return [2] * 4
    elif layer_str.startswith("("):
        nums = layer_str.strip("()").replace(" ", "").split(",")
        widths = []
        for n in nums:
            if n == "2": widths.extend([1, 1])
            elif n == "1": widths.append(2)
        return widths
    return []

# 1. Load the real medications from the SSRS sample
df = pd.read_csv("sample_ssrs.csv", skiprows=2)
# Clean columns
df.columns = [str(c).strip() for c in df.columns]

# Extract unique medications
medications = df['ARTICLE NAME'].dropna().unique().tolist()

# 2. Map medications to physical bins
master_data = []
med_index = 0

for shelf_name, config in shelf_configs.items():
    bin_counter = 1
    for layer in config:
        if layer == "TABLE": continue
        widths = parse_layer(layer)
        for w in widths:
            bin_id = f"Bin {bin_counter}"
            
            # If we still have medications left in our sample, assign it
            if med_index < len(medications):
                med = medications[med_index]
                
                # Mock some realistic PAR levels
                max_cap = random.randint(100, 1000)
                item_type = random.choice(["Fast-Moving", "Slow-Moving"])
                
                if item_type == "Fast-Moving":
                    reorder_t = 0
                    topup_t = int(max_cap * 0.4)
                else:
                    reorder_t = int(max_cap * 0.3)
                    topup_t = 0
                
                master_data.append({
                    "Shelf": shelf_name,
                    "Bin": bin_id,
                    "Medication": med,
                    "Type": item_type,
                    "Max_Capacity": max_cap,
                    "Reorder_Threshold": reorder_t,
                    "TopUp_Threshold": topup_t
                })
                med_index += 1
            
            bin_counter += 1

master_df = pd.DataFrame(master_data)
master_df.to_csv("master_config.csv", index=False)
print(f"Successfully created master_config.csv mapping {len(master_df)} medications to physical bins.")
