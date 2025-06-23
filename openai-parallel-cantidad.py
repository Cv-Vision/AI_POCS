import os
import random
import re
import threading
import time
import uuid
import fitz
import PIL.Image
from dotenv import load_dotenv
import base64
import json
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

load_dotenv()

model = "gpt-4.1-mini"
casos = ["diseño_grafico", "docente", "ejecutivo_influencers"]
batch_sizes = [10, 30,50]
cantidad_casos = 6



client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

lock = threading.Lock()

BATCH_SIZE = 10
DELAY_AFTER_BATCH = 60


# Leer archivos PDF
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def pdf_to_png_bytes(pdf_path, page_number=0):
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=150)
        image = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def image_file_to_bytes(image_path):
    with PIL.Image.open(image_path) as img:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()


def count_tokens(text):
    return len(text) // 4


def load_prompt_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: El archivo de prompt '{file_path}' no fue encontrado.")
        exit()
    except Exception as e:
        print(f"Error al leer el archivo de prompt '{file_path}': {e}")
        exit()


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


def find_cv_path(cv_dir, cv_filename):
    possible_paths = [
        os.path.join(cv_dir, "si", cv_filename),
        os.path.join(cv_dir, "no", cv_filename)
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"❌ Archivo {cv_filename} no encontrado en {cv_dir}/si ni en {cv_dir}/no")



def process_cvs(filenames, cv_dir, job_description_file, prompt_file_path, output_json_file):

    job_description = extract_text_from_pdf(job_description_file)

    prompt_template = load_prompt_from_file(prompt_file_path)
    prompt_base = prompt_template.replace("{job_description}", job_description)

    participant_ids = [str(uuid.uuid4()) for _ in filenames]

    prompt = prompt_base + "\n" + "\n".join(participant_ids)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
    ]

    for cv_filename in filenames:
        cv_path = find_cv_path(cv_dir, cv_filename)
        ext = os.path.splitext(cv_filename)[1].lower()

        # Convert to PNG bytes
        if ext == ".pdf":
            image_bytes = pdf_to_png_bytes(cv_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            image_bytes = image_file_to_bytes(cv_path)
        else:
            print(f"⚠️ Ignorando archivo no compatible: {cv_filename}")
            return

        messages[0]["content"].append(
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8")
                }
            }
        )

    try:

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2
        )

        print("✅ Respuesta recibida")
        response_text = response.choices[0].message.content

        with lock:
            print(f"✅ Procesado: {cv_filename}")

            existing_data = []
            if os.path.exists(output_json_file):
                with open(output_json_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        pass

            json_blocks = re.findall(r'```json\n(.*?)```', response_text, re.DOTALL)

            for block in json_blocks:
                result = json.loads(block)
                existing_data.append(result)

            with open(output_json_file, "w") as f:
                json.dump(existing_data, f, indent=2)

    except Exception as e:
        print(f"❌ Error procesando {cv_filename}: {e}")


# with ThreadPoolExecutor() as executor:
#     for caso in casos:
#         for i in range(cantidad_casos):
#             caso_actual = i + 1
#             prueba = f"sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{caso_actual}/"
#             job_description_file = prueba + "job_description.pdf"
#             prompt_file_path = prueba + "prompt.txt"
#             cvs_path = prueba + "cvs/"
#             cvs_yes_path = cvs_path + "si"
#             cvs_no_path = cvs_path + "no"
#
#             futures = []
#
#             for idx, size in enumerate(batch_sizes):
#                 size_index = idx + 1
#                 output_json_file = prueba + f"output-set{size}.json"
#
#                 if caso_actual == 1:
#                     # Relevant & Irrelevant CVs mixed 50/50
#                     cvs = select_mixed_cvs(cvs_yes_path, cvs_no_path, size)
#                 elif caso_actual == 2:
#                     # Repeated CVs from the "yes" folder
#                     cvs = select_repeated_cvs(cvs_yes_path, size)
#                 elif caso_actual == 3:
#                     # Only Relevant CVs
#                     cvs = select_cvs_of_one_kind(cvs_yes_path, size)
#                 elif caso_actual == 4:
#                     # Only Irrelevant CVs
#                     cvs = select_cvs_of_one_kind(cvs_no_path, size)
#                 elif caso_actual == 5:
#                     # Some corrupted or empty CVs
#                     cvs = select_most_cvs_of_one_kind(cvs_yes_path, cvs_no_path, size, size_index)
#                 else:
#                     # Generic JD
#                     cvs = select_cvs_of_one_kind(cvs_yes_path, size)
#
#                 futures.append(executor.submit(
#                     process_cvs, cvs, cvs_path, job_description_file, prompt_file_path, output_json_file
#                 ))
#
#             for future in as_completed(futures):
#                 try:
#                     future.result()
#                 except Exception as e:
#                     print(f"❌ Error en future: {e}")
#
#             print(f"✅ Terminado caso {caso_actual} de {caso}, esperando {DELAY_AFTER_BATCH} segundos...")
#             time.sleep(DELAY_AFTER_BATCH)

with ThreadPoolExecutor() as executor:
    caso = "admin_finanzas"
    caso_actual = 3
    prueba = f"sets_de_pruebas/pruebas_de_cantidad/{caso}/caso{caso_actual}/"
    job_description_file = prueba + "job_description.pdf"
    prompt_file_path = prueba + "prompt.txt"
    cvs_path = prueba + "cvs/"
    cvs_yes_path = cvs_path + "si"
    cvs_no_path = cvs_path + "no"

    futures = []

    new_sizes = [10, 30, 50]

    for idx, size in enumerate(new_sizes):
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

        futures.append(executor.submit(
            process_cvs, cvs, cvs_path, job_description_file, prompt_file_path, output_json_file
        ))

    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"❌ Error en future: {e}")

    print(f"✅ Terminado caso {caso_actual} de {caso}, esperando {DELAY_AFTER_BATCH} segundos...")
    time.sleep(DELAY_AFTER_BATCH)
