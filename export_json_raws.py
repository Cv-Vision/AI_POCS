import os
import json
import pandas as pd


def extract_quality_scores_to_excel(casos, cantidad_casos, cantidad_sets, output_excel_file):
    columns = {}

    for caso in casos:
        for cantidad_caso in range(1, cantidad_casos +1):
            for cantidad_set in range(1, cantidad_sets + 1):
                scores = []
                json_dir = f"pruebas_mirko/sets_de_pruebas/pruebas_de_calidad/{caso}/caso{cantidad_caso}/set{cantidad_set}/"
                column_name = f"{caso}_caso{cantidad_caso}_set{cantidad_set}"
                if not os.path.exists(json_dir):
                    continue

                for file_name in os.listdir(json_dir):
                    if file_name.endswith(".json"):
                        file_path = os.path.join(json_dir, file_name)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                            for entry in data:
                                scores.append(entry.get("score", None))
                columns[column_name] = scores

    df = pd.DataFrame(columns)
    df.to_excel(output_excel_file, index=False)


def extract_quantity_scores_to_excel(casos, cantidad_casos, cantidad_sets, output_excel_file):
    columns = {}

    for caso in casos:
        for cantidad_caso in range(1, cantidad_casos +1):
            for cantidad_set in cantidad_sets:
                scores = []
                json_dir = f"pruebas_mirko/sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{cantidad_caso}/"
                column_name = f"{caso}_caso{cantidad_caso}_set{cantidad_set}"
                if not os.path.exists(json_dir):
                    continue

                file_path = os.path.join(json_dir, f"output-set{cantidad_set}.json")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for entry in data:
                    scores.append(entry.get("score", None))
                columns[column_name] = scores

    max_length = max(len(scores) for scores in columns.values())
    for key in columns:
        columns[key].extend([None] * (max_length - len(columns[key])))

    df = pd.DataFrame(columns)
    df.to_excel(output_excel_file, index=False)


output_file = "raw_jsons_cantidad_gemini.xlsx"
casos = ["admin_finanzas", "cuentas_digitales", "diseño_grafico", "docente", "ejecutivo_influencers"]
cantidad_casos = 6
cantidad_sets = [10,30,50]
extract_quantity_scores_to_excel(casos, cantidad_casos, cantidad_sets, output_file)