import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

# Carica le variabili dal file .env nella cartella del progetto
load_dotenv()


def main():
    # 1) Leggiamo host e porta SMTP dalle variabili d'ambiente (con default sensati)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    # 2) Leggiamo credenziali e destinatario (se mancano -> errore subito, così te ne accorgi)
    user = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    to = os.environ["EMAIL_TO"]

    # 3) Costruiamo l'email
    msg = EmailMessage()
    msg["Subject"] = "Buona scuola"
    msg["From"] = user
    msg["To"] = to
    msg.set_content("Buona scuola! ✅")

    # 4) Connessione al server SMTP e invio
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        number = 0
        server.starttls()              # attiva cifratura TLS
        server.login(user, password)   # login al server
        while number < 10:
            number += 1
            server.send_message(msg)       # invia email


if __name__ == "__main__":
    main()
