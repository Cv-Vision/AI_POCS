import json
import os.path
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


def change_len_to_x(json_path, x):
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as _:
            data = []
            fill_with_empty(json_path)

    if not isinstance(data, list):
        print("Error: The JSON file must contain a list at the top level.")
        return

    if len(data) == x:
        return

    if len(data) < x:
        print(json_path)
        print(f"Error: JSON file contains only {len(data)} entries, less than {x}.")
        print("---------------------------------")
        return

    x = int(x)
    y = len(data) - x

    new_data = data[y:]

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"Removed the first {x} entries. New length: {len(new_data)}")

def fill_with_empty(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        try :
            json.load(f)
        except json.JSONDecodeError as e:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)


def flatten_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        flattened = []
        for item in data:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)

        if data != flattened:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(flattened, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
        casos = ["admin_finanzas", "cuentas_digitales", "diseño_grafico", "docente", "ejecutivo_influencers"]
        cantidad_casos = 6
        sets = [10,30,50]
        for caso in casos:
            for cantidad_caso in range(1, cantidad_casos + 1):
                if not os.path.exists(f"pruebas_mirko/sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{cantidad_caso}"):
                    continue
                for cantidad_set in sets:
                    file = f"pruebas_mirko/sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{cantidad_caso}/output-set{cantidad_set}.json"
                    change_len_to_x(file, cantidad_set)
