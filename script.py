import json
import sys

def analyze_scores(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    above_50 = sum(1 for entry in data if entry.get("score", 0) >= 60)
    below_or_equal_50 = total - above_50

    print(f"Total entries: {total}")
    print(f"Score > 50: {above_50}")
    print(f"Score ≤ 50: {below_or_equal_50}")

def remove_first_x(json_path, x):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: The JSON file must contain a list at the top level.")
        return

    x = int(x)
    if x >= len(data):
        print(f"Removing all {len(data)} entries. Result will be an empty list.")
        new_data = []
    else:
        new_data = data[x:]

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"Removed the first {x} entries. New length: {len(new_data)}")

if __name__ == "__main__":
        analyze_scores("sets_de_pruebas/pruebas_de_cantidad/ejecutivo_influencers/caso4/output-set50.json")
