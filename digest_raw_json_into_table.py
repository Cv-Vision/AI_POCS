import pandas as pd
import re


def digest_raw_quality_json_into_table(file_path, output_file):
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    df = pd.read_excel(file_path, sheet_name=sheets[0])

    results = []
    for col in df.columns:
        match = re.match(r"(.*)_caso(\d+)_set(\d+)", col)
        if match:
            area = match.group(1).replace("_", " ").title()
            caso = int(match.group(2))
            set_ = int(match.group(3))
            total_pruebas = 10  # Fixed value
            scores = df[col].dropna()
            media_score = scores.mean()
            desviacion_score = scores.std()

            results.append({
                "Área de postulación": area,
                "Caso evaluado": caso,
                "Set evaluado": set_,
                "Total pruebas": total_pruebas,
                "Anomalías o problemas": "-",
                "Media de Score": media_score,
                "Desviación de Score": desviacion_score
            })

    summary_df = pd.DataFrame(results)
    summary_df.to_excel(output_file, index=False)


def digest_raw_quantity_json_into_table(file_path, output_file):
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    df = pd.read_excel(file_path, sheet_name=sheets[0])

    results = []
    for col in df.columns:
        match = re.match(r"(.*)_caso(\d+)_set(\d+)", col)
        if match:
            area = match.group(1).replace("_", " ").title()
            caso = int(match.group(2))
            set_ = int(match.group(3))
            scores = df[col].dropna()
            relevants = 0
            irrelevants = 0
            unknowns = 0
            for score in scores:
                if score >= 80:
                    relevants += 1
                elif score <= 30:
                    irrelevants += 1
                else:
                    unknowns += 1


            if caso == 1:
                caso_evaluado = "CVs de Industria mezclados 50/50"
            elif caso == 2:
                caso_evaluado = "CVs Repetidos de la carpeta 'Sí'"
            elif caso == 3:
                caso_evaluado = "Solo CVs Relevantes"
            elif caso == 4:
                caso_evaluado = "Solo CVs Irrelevantes"
            elif caso == 5:
                caso_evaluado = "Algunos CVs Corruptos"
            else:
                caso_evaluado = "JD genérica"

            results.append({
                "Área de postulación": area,
                "Caso evaluado": caso_evaluado,
                "Tamaño del Batch": set_,
                "Candadiatos Relevantes": relevants,
                "Candadiatos Irrelevantes": irrelevants,
                "Candadiatos Inciertos": unknowns,
                "Anomalías o problemas": "-",
                "Conclusión de efectividad": "-"
            })

    summary_df = pd.DataFrame(results)
    summary_df.to_excel(output_file, index=False)


if __name__ == "__main__":
    file_path = "raw_jsons_cantidad_gpt.xlsx"
    output_file = "summary_output_cantidad_gpt.xlsx"
    digest_raw_quantity_json_into_table(file_path, output_file)