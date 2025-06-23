import os
import threading
import dotenv
import uuid
import json
from affinda import AffindaAPI, TokenCredential
from concurrent.futures import ThreadPoolExecutor

dotenv.load_dotenv()

workspace = os.getenv("AFFINDA_WORKSPACE_ID", None)
candidate_document_type_id = os.getenv("CANDIDATE_DOCUMENT_TYPE_ID")
job_posting_document_type_id = os.getenv("JOB_POSTING_DOCUMENT_TYPE_ID")

client = AffindaAPI(credential=TokenCredential(token=os.getenv("AFFINDA_API_KEY")))
lock = threading.Lock()

casos = ["admin_finanzas", "diseño_grafico", "ejecutivo_cuentas_digitales", "ejecutivo_influencers","ingenieria_informatica", "rrhh", "tecnico_mantenimiento"]
cantidad_casos = 5
cantidad_sets = 3

def upload_document(file_path, document_type):
    with open(file_path, "rb") as f:
        doc = client.create_document(
            file=f,
            workspace=workspace,
            document_type=document_type,
            wait=True,
            delete_after_parse=True,
            use_ocr=True,
        )
    return doc.meta.identifier


def match_cvs_to_job(cv_paths, jd_path):
    try:
        jd_id = upload_document(jd_path,job_posting_document_type_id)
        print("job description id:", jd_id)
        cv_ids = [upload_document(cv_path, candidate_document_type_id) for cv_path in cv_paths]
        print("cv ids:", cv_ids)

        match_result = client.create_job_description_search({
            "job_description": jd_id,
            "documents": cv_ids,
            "indices": list(range(len(cv_ids)))
        })

        results = []
        for idx, match_data in enumerate(match_result.results):
            results.append(
                {
                    "participant_id": str(uuid.uuid4()),
                    "score": match_data.score,
                    "highlights": match_data.highlights,
                    "match_details": [m.to_dict() for m in match_data.match_details]
                }
            )

        return results

    except Exception as e:
        print(f"❌ Error matching {cv_paths} to {jd_path}: {e}")
        return None


def process_cv(cv_filenames, cv_dir, job_description_file, output_json_file):
    cv_paths = [os.path.join(cv_dir, cv_filename) for cv_filename in cv_filenames]

    results = match_cvs_to_job(cv_paths, job_description_file)

    if results:
        with lock:
            print(f"✅ Procesado: {cv_filenames} para {job_description_file}")
            existing_data = []
            if os.path.exists(output_json_file):
                with open(output_json_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        pass

            existing_data.extend(results)

            with open(output_json_file, "w") as f:
                json.dump(existing_data, f, indent=2)


with ThreadPoolExecutor() as executor:
    for caso in casos:
        for i in range(cantidad_casos):
            prueba = f"sets_de_pruebas/pruebas_de_calidad/{caso}/caso{i + 1}/"
            for j in range(cantidad_sets):
                set = "set" + str(j + 1) + "/"
                cv_dir = prueba + set + "cvs"
                job_description_file = prueba + set + "job_description.pdf"
                output_json_file = prueba + set + "output-set" + str(j + 1) + ".json"
                file = next((f for f in os.listdir(cv_dir) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))),None)

                executor.submit(process_cv, [file], cv_dir, job_description_file, output_json_file)