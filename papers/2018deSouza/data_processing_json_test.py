import json
import pandas as pd

def load_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)
    
def data_to_dataframe(site_data):
    all_structures = [structure for structures in site_data.values() for structure in structures]
    df = pd.DataFrame(all_structures)
    return df

    # for site, structures in site_data.items():
    #     print(f"{site}: {len(structures)} structures")

if __name__ == "__main__":
    filename = "2018deSouza_sites.json"
    site_data = load_data(filename)
    df = data_to_dataframe(site_data)

    
    print(df.head(10))
    print("\nSummary stats:")
    print(df.describe(include="all"))