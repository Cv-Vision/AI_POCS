import os
import random
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
batch_sizes = [10, 30,50]
cantidad_casos = 6

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


def select_cvs_of_one_kind(cvs_path, size):
    cvs = os.listdir(cvs_path)
    random.shuffle(cvs)

    selected_cvs = cvs[:size]
    return selected_cvs


def select_most_cvs_of_one_kind(cvs_of_kind_path, cvs_of_alternative_kind_path, size, size_index):
    kind_count = size - size_index + 1
    alternative_count = size - kind_count

    cvs_kind = os.listdir(cvs_of_kind_path)
    cvs_alternative = os.listdir(cvs_of_alternative_kind_path)

    random.shuffle(cvs_kind)
    random.shuffle(cvs_alternative)

    selected_cvs = []
    selected_yes_cvs = cvs_kind[:kind_count]
    selected_no_cvs = cvs_alternative[:alternative_count]

    selected_cvs.extend(selected_yes_cvs)
    selected_cvs.extend(selected_no_cvs)

    return selected_cvs


def select_mixed_cvs(cvs_yes_path, cvs_no_path, size):
    cvs_yes = os.listdir(cvs_yes_path)
    cvs_no = os.listdir(cvs_no_path)

    random.shuffle(cvs_yes)
    random.shuffle(cvs_no)
    half_size = size // 2

    selected_cvs = []
    selected_cvs.extend(cvs_yes[:half_size])
    selected_cvs.extend(cvs_no[:half_size])

    return selected_cvs


def select_repeated_cvs(cvs_yes_path, size):
    cvs_yes = os.listdir(cvs_yes_path)
    random.shuffle(cvs_yes)

    half_size = size // 2
    selected_cvs = cvs_yes[:half_size]

    repeated = []
    for cv in selected_cvs:
        repeated.extend([cv, cv])

    return repeated


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
            caso_actual = i + 1
            prueba = f"sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{caso_actual}/"
            job_description_file = prueba + "job_description.pdf"
            prompt_file_path = prueba + "prompt.txt"
            cvs_path = prueba + "cvs/"
            cvs_yes_path = cvs_path + "si"
            cvs_no_path = cvs_path + "no"

            for idx, size in enumerate(batch_sizes):
                size_index = idx + 1
                output_json_file = prueba + f"output-set{size}.json"

                if caso_actual == 1:
                    # Relevant & Irrelevant CVs mixed 50/50
                    cvs = select_mixed_cvs(cvs_yes_path, cvs_no_path, size)
                elif caso_actual == 2:
                    # Repeated CVs from the "yes" folder
                    cvs = select_repeated_cvs(cvs_yes_path, size)
                elif caso_actual == 3:
                    # Only Relevant CVs
                    cvs = select_cvs_of_one_kind(cvs_yes_path, size)
                elif caso_actual == 4:
                    # Only Irrelevant CVs
                    cvs = select_cvs_of_one_kind(cvs_no_path, size)
                elif caso_actual == 5:
                    # Some corrupted or empty CVs
                    cvs = select_most_cvs_of_one_kind(cvs_yes_path, cvs_no_path, size, size_index)
                else:
                    # Generic JD
                    cvs = select_cvs_of_one_kind(cvs_yes_path, size)

                executor.submit(process_cv, cvs, cvs_path, job_description_file, output_json_file)