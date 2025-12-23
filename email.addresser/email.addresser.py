import os
import ssl
import smtplib
from email.message import EmailMessage


def require_env(name: str) -> str:
    """Legge una variabile d'ambiente obbligatoria, altrimenti errore chiaro."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing env var: {name}. "
            f"Su GitHub Actions mettila nei repository secrets e poi in env."
        )
    return value


def build_message(sender: str, recipient: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    return msg


def main() -> None:
    # SMTP (opzionali)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    timeout = int(os.getenv("SMTP_TIMEOUT", "30"))

    # Credenziali/destinatario (obbligatori, tipicamente da GitHub Secrets)
    user = require_env("EMAIL_USER")
    password = require_env("EMAIL_PASS")
    to = require_env("EMAIL_TO")

    # Opzioni invio
    count = int(os.getenv("EMAIL_COUNT", "10"))
    debug = os.getenv("SMTP_DEBUG", "0") == "1"

    # Metadati utili su GitHub Actions (se presenti)
    run_id = os.getenv("GITHUB_RUN_ID", "")
    sha = os.getenv("GITHUB_SHA", "")

    # Connessione + invio
    context = ssl.create_default_context()

    with smtplib.SMTP(host=smtp_host, port=smtp_port, timeout=timeout) as server:
        if debug:
            server.set_debuglevel(1)

        # Importante: EHLO -> STARTTLS -> EHLO
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()

        server.login(user, password)

        for i in range(1, count + 1):
            subject = "Buona scuola"
            body = "Buona scuola! ✅"

            # Se vuoi, aggiungi info run per tracciare (utile in CI)
            if run_id or sha:
                body += f"\n\n(GitHub Actions run: {run_id} | sha: {sha[:7]})"

            msg = build_message(user, to, subject, body)
            server.send_message(msg)

            print(f"Sent {i}/{count} to {to}")


if __name__ == "__main__":
    main()
