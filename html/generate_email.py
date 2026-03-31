import random

# Lista immagini
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

# URL base (CAMBIALO con il tuo dominio reale)
BASE_URL = "https://github.com/tommiigemii/email.project/tree/main/html/elementi/anteprima"

# Scelta random
random_image = random.choice(immagini)
image_url = BASE_URL + random_image

# Leggi template
with open("email_template.html", "r", encoding="utf-8") as file:
    html = file.read()

# Sostituzioni
html = html.replace("{{RANDOM_IMAGE_URL}}", image_url)
html = html.replace("{{NAME}}", "Guesus")
html = html.replace("{{FRASE_MATTINO}}", "Disciplina batte motivazione.")
html = html.replace("{{LINK_3D}}", "https://tuo-link-3d.com")

# Salva output
with open("output_email.html", "w", encoding="utf-8") as file:
    file.write(html)

print("Email generata con immagine:", image_url)
