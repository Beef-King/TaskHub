import smtplib
from email.mime.text import MIMEText

EMAIL_ADDRESS = "mabelime51@gmail.com"
EMAIL_PASSWORD = "clxs qzty xwyh wjei"


def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"TaskHub <{EMAIL_ADDRESS}>"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    send_email(
        "mabelime32@gmail.com",
        "TaskHub Test",
        "If you're reading this, email sending works!"
    )