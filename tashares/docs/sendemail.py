from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import smtplib
import os
from datetime import datetime


def send_mail(csv_files):
    # Create a multipart message
    msg = MIMEMultipart()
    body_part = MIMEText('FYI', 'plain')
    msg['Subject'] = f"stock ta {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = 'youremail@gmail.com'
    recipients = ['youremail@gmail.com', ]
    msg['To'] = ", ".join(recipients)
    # Add body to email
    msg.attach(body_part)

    # loop over files
    for file in csv_files:
        with open(file, 'rb') as f:
            # Attach the file with filename to the email
            msg.attach(MIMEApplication(f.read(), Name=os.path.split(file)[-1]))

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login('youremail@gmail.com', 'yourpasscode')
    server.sendmail(msg['From'], recipients, msg.as_string())
    server.quit()


if __name__ == '__main__':

    csv_files = [f"file_one.csv",
                 f"file_two.csv"]
    send_mail(csv_files)
