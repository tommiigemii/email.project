import random
import os

# =========================
# LISTA IMMAGINI
# =========================

immagini = [
    "00D69833-C09F-4DE3-ADC4-3A4F8B0C704E_236487F7-1C83-48CC-A8FC-098C2030B886.jpeg",
    "504b11f5-ba4d-46a7-81f5-3a9b6804aae3.jpeg",
    "832D51EE-01DA-45FF-921F-30D912D01F64_BCAE311A-3744-465B-AE92-BD37A0DCA339.jpeg",
    "B7888349-454A-4D30-A29A-16602651CF9B.jpeg",
    "IMG_2426.jpeg",
    "IMG_2457.jpeg",
    "IMG_2610.png",
    "IMG_2884.jpeg",
    "IMG_2966.jpeg",
    "IMG_2982.png",
    "IMG_3059.jpeg",
    "IMG_3157.jpeg",
    "IMG_3248.jpeg",
    "IMG_3357.jpeg",
    "IMG_3370.jpeg",
    "IMG_3394.jpeg",
    "IMG_3666.jpeg",
    "image.jpeg",
    "photo-2299_singular_display_fullPicture.jpeg",
    "photo-2914_singular_display_fullPicture.jpeg",
    "photo-3355_singular_display_fullPicture.jpeg"
]

# =========================
# ⚠️ URL PUBBLICO (CORRETTO)
# =========================

BASE_URL = "https://raw.githubusercontent.com/tommiigemii/email.project/main/html/elementi/anteprima/"

# =========================
# PATH FILE (CORRETTI)
# =========================

TEMPLATE_PATH = "html/template_email.html"
OUTPUT_PATH = "html/output_email.html"

# =========================
# SCELTA IMMAGINE
# =========================

random_image = random.choice(immagini)
image_url = BASE_URL + random_image

print("📸 Immagine scelta:", image_url)

# =========================
# LETTURA TEMPLATE
# =========================

if not os.path.isfile(TEMPLATE_PATH):
    raise Exception(f"Template non trovato: {TEMPLATE_PATH}")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
    html = file.read()

# =========================
# SOSTITUZIONI
# =========================

html = html.replace("{{RANDOM_IMAGE_URL}}", image_url)
html = html.replace("{{NAME}}", os.getenv("NAME", "Guesus"))
html = html.replace("{{FRASE_MATTINO}}", os.getenv("FRASE_MATTINO", "Disciplina batte motivazione."))
html = html.replace("{{LINK_3D}}", os.getenv("LINK_3D", "https://tuo-link-3d.com"))

# =========================
# SALVATAGGIO OUTPUT
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    file.write(html)

print("✅ Email generata correttamente!")
