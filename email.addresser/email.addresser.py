import os
import re
import ssl
import smtplib
import random
from email.message import EmailMessage
from typing import List, Dict

# ✅ Niente dotenv: su GitHub Actions userai i Secrets come variabili d’ambiente
# (Settings → Secrets and variables → Actions → New repository secret)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def leggi_obbligatoria(nome_variabile: str) -> str:
    valore = os.getenv(nome_variabile)
    if not valore:
        raise RuntimeError(
            f"Variabile mancante: {nome_variabile}. "
            f"Controlla che esista come Repository Secret / Environment Variable su GitHub Actions."
        )
    return valore


def email_valida(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def html_to_text(html: str) -> str:
    testo = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.I)
    testo = re.sub(r"</\s*p\s*>", "\n", testo, flags=re.I)
    testo = re.sub(r"</\s*div\s*>", "\n", testo, flags=re.I)
    testo = re.sub(r"<[^>]+>", "", testo)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return testo.strip()


def leggi_template_corpo() -> str:
    """
    Su GitHub Actions:
    - Consigliato: metti il template in repo (template_email.html) e setta EMAIL_BODY_FILE=template_email.html
    - Oppure metti EMAIL_BODY come secret (ma è scomodo perché multilinea)
    """
    path = os.getenv("EMAIL_BODY_FILE", "").strip()
    if path:
        if not os.path.exists(path):
            raise RuntimeError(f"EMAIL_BODY_FILE punta a un file inesistente nel repo: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return leggi_obbligatoria("EMAIL_BODY")


def compila_double_curly(template: str, dati: Dict[str, str]) -> str:
    """
    Compila placeholder stile: {{NAME}}, {{ADMIN}}, {{FRASE_MATTINO}}, {{LINK_3D}}, {{IMG_PREVIEW}}
    """
    out = template
    for k, v in dati.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def parse_destinatari(stringa_destinatari: str) -> List[Dict[str, str]]:
    blocchi = [b.strip() for b in stringa_destinatari.split(";") if b.strip()]
    out: List[Dict[str, str]] = []

    for blocco in blocchi:
        parti = [p.strip() for p in blocco.split("|") if p.strip()]
        if len(parti) < 2:
            print(f"[WARN] Ignorato (formato non valido): '{blocco}'. Usa: email|nome")
            continue

        email, name = parti[0], parti[1]
        if not email_valida(email):
            print(f"[WARN] Ignorato (email non valida): '{email}'")
            continue

        out.append({"email": email, "name": name})

    if not out:
        raise RuntimeError("Nessun destinatario valido trovato. Controlla EMAIL_RECIPIENTS nei Secrets.")
    return out


def scegli_frasi(destinatari_n: int, frasi: List[str]) -> List[str]:
    if not frasi:
        raise RuntimeError("Lista frasi_mattino vuota.")
    if destinatari_n <= len(frasi):
        return random.sample(frasi, k=destinatari_n)  # tutte diverse (finché possibile)
    return [random.choice(frasi) for _ in range(destinatari_n)]


def costruisci_messaggio(mittente: str, destinatario: str, soggetto: str, corpo_html: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = mittente
    msg["To"] = destinatario
    msg["Subject"] = soggetto

    msg.set_content(html_to_text(corpo_html))
    msg.add_alternative(corpo_html, subtype="html")
    return msg


def invia_email(
    host_smtp: str,
    porta_smtp: int,
    utente_email: str,
    password_email: str,
    email_pronte: List[Dict[str, str]],
) -> None:
    contesto_ssl = ssl.create_default_context()

    with smtplib.SMTP(host=host_smtp, port=porta_smtp, timeout=30) as server:
        server.ehlo()
        server.starttls(context=contesto_ssl)
        server.ehlo()

        server.login(utente_email, password_email)

        for i, e in enumerate(email_pronte, start=1):
            msg = costruisci_messaggio(
                mittente=utente_email,
                destinatario=e["email"],
                soggetto=e["subject"],
                corpo_html=e["body_html"],
            )
            server.send_message(msg)
            print(f"Inviata {i}/{len(email_pronte)} a {e['name']} <{e['email']}>")


def main() -> None:
    # ✅ Niente load_dotenv()

    # Secrets / env vars (GitHub Actions)
    utente_email = leggi_obbligatoria("EMAIL_USER")
    password_email = leggi_obbligatoria("EMAIL_PASS")

    # Admin (puoi metterlo come secret ADMIN, oppure lasciare default)
    admin = os.getenv("ADMIN", "Admin")

    # Destinatari: mettilo come secret EMAIL_RECIPIENTS
    stringa_destinatari = os.getenv("EMAIL_RECIPIENTS") or os.getenv("EMAIL_RECIPIENT")
    if not stringa_destinatari:
        raise RuntimeError("Manca EMAIL_RECIPIENTS nei Secrets (es: mail|nome;mail|nome).")

    soggetto_template = leggi_obbligatoria("EMAIL_SUBJECT")
    corpo_template = leggi_template_corpo()

    host_smtp = os.getenv("SMTP_HOST", "smtp.gmail.com")
    porta_smtp = int(os.getenv("SMTP_PORT", "587"))

    # Link GitHub Pages + preview (URL pubblico)
    link_3d = leggi_obbligatoria("LINK_3D")         # es: https://tuonome.github.io/3d-viewer/
    img_preview = leggi_obbligatoria("IMG_PREVIEW") # es: https://tuonome.github.io/3d-viewer/preview.gif

    # Frasi
    frasi_mattino = [
        "Buongiorno mondo, oggi tolleranza zero ma sorriso finto.",
        "Mi sveglio stanco ma ambizioso (più o meno).",
        "Oggi faccio il minimo indispensabile con grande stile.",
        "Non sono in ritardo, sono in modalità narrativa.",
        "Caffè entrato, personalità non ancora caricata.",
        "Oggi vibrazioni positive, domani vediamo.",
        "Non so cosa sto facendo ma lo faccio con sicurezza.",
        "Buongiorno a chi ce la fa, io intanto respiro.",
        "Main character energy finché non apro WhatsApp.",
        "Sono produttivo dentro, fuori meno.",
        "Oggi tutto easy (bugia).",
        "La motivazione arriverà, forse, con il secondo caffè.",
        "Mi alzo forte ma con rispetto.",
        "Sto dando il massimo emotivamente (cioè poco).",
        "Oggi faccio cose, alcune inutili, altre pure.",
        "Ansia sotto controllo (non vero ma ci credo).",
        "Buongiorno solo se necessario.",
        "Oggi grind leggero, sopravvivenza pesante.",
        "Sono calmo perché ho rinunciato a capire.",
        "Oggi vibes alte, aspettative basse.",
        "Mi sento iconico ma confuso.",
        "Sto vivendo la mia era del fare finta di avere tutto chiaro.",
        "Sveglio sì, lucido no.",
        "Oggi niente drammi, solo micro-crisi.",
        "Sono pronto a dare il 30 percento di me stesso.",
        "Mood: vediamo che succede.",
        "Oggi non mollo, al massimo rimando.",
        "Buongiorno ma senza entusiasmo eccessivo.",
        "Ho dormito? Sì. Bene? Dibattibile.",
        "Oggi esisto con convinzione."
    ]

    destinatari = parse_destinatari(stringa_destinatari)
    frasi_assegnate = scegli_frasi(len(destinatari), frasi_mattino)

    email_pronte: List[Dict[str, str]] = []
    for d, frase in zip(destinatari, frasi_assegnate):
        # Subject: usa {admin} e {name}
        subject = soggetto_template.format(admin=admin, name=d["name"])

        dati_html = {
            "NAME": d["name"],
            "ADMIN": admin,
            "FRASE_MATTINO": frase,
            "LINK_3D": link_3d,
            "IMG_PREVIEW": img_preview,
        }
        body_html = compila_double_curly(corpo_template, dati_html)

        email_pronte.append(
            {"name": d["name"], "email": d["email"], "subject": subject, "body_html": body_html}
        )

    invia_email(host_smtp, porta_smtp, utente_email, password_email, email_pronte)


if __name__ == "__main__":
    main()
