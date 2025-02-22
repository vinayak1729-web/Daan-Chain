import os
import random
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from signupEmailBody import Sign_up_email_body_template
from dotenv import load_dotenv

load_dotenv()
email_sender = os.getenv('EMAIL_USER')
sender_password = os.getenv('EMAIL_PASS')


def generate_otp():
    """Generates a 6-digit random OTP."""
    return str(random.randint(100000, 999999))

def send_sign_up_email(recipient_email, username, sender_email, sender_password , body):
    """Sends a formatted HTML email with OTP for signup verification."""

    otp = generate_otp() # Generate OTP here
    subject = "Surya Prabha - Verify Your Email to Activate Your Account" # Improved Subject

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.sendmail(sender_email, recipient_email, message.as_string())
        print(f"Verification email sent successfully to {username} ({recipient_email}) with OTP: {otp}") # Print OTP for debugging

    except Exception as e:
        print(f"Error sending email: {e}")

