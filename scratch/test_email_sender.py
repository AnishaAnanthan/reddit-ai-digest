import sys
import os

# Ensure app directory is in path
sys.path.append(os.getcwd())

from app.services.notifications.email_sender import send_results_email

def test_email():
    print("Attempting to send test email...")
    test_body = "This is a test email from the Reddit AI Agent to verify email functionality."
    try:
        send_results_email(test_body)
        print("Success! Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

if __name__ == "__main__":
    test_email()
