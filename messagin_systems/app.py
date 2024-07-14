from flask import Flask, request, Response
from celery import Celery
import smtplib
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app and Celery
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://localhost//'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

# Email credentials
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Get the directory path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the log file
LOG_FILE_PATH = os.path.join(script_dir, 'messaging_system.log')

# Configure logging
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO)

@celery.task
def send_email(recipient, subject, body):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(EMAIL_USERNAME, recipient, message)
    logging.info(f"Email sent to {recipient}")

@app.route("/")
def index():
    return "Welcome to the Messaging System!"

@app.route("/sendmail")
def send_mail():
    recipient = request.args.get('recipient')
    subject = request.args.get('subject', 'No Subject')
    body = request.args.get('body', 'No Content')
    
    send_email.delay(recipient, subject, body)
    return "Email sending initiated!"

@app.route("/talktome")
def log_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE_PATH, "a") as f:
        f.write(f"{current_time}\n")
    logging.info(f"Current Time: {current_time}")
    return "Logged current time."

@app.route("/logs")
def view_logs():
    try:
        with open(LOG_FILE_PATH, "r") as log_file:
            log_content = log_file.read()
        return Response(log_content, mimetype='text/plain')
    except FileNotFoundError:
        return "Log file not found.", 404
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
