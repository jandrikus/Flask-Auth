# This module implements email helper for Auth.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from flask import redirect, url_for, current_app, render_template
from flask_babel import _
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid

def send_email(subject, receiver, plain_text, html_text = '', replyr = None, sender = None):
	msg = EmailMessage()
	msg['Date'] = datetime.utcnow()+timedelta(hours=1)
	msg['Message-ID'] = make_msgid()
	msg['Subject'] = subject
	print(current_app.auth.AUTH_EMAIL_SENDER_PASSWORD)
	if sender:
		msg['From'] = Address(sender[0], sender[1].split('@')[0], sender[1].split('@')[1])
	else:
		msg['From'] = Address(current_app.auth.AUTH_EMAIL_SENDER_NAME, current_app.auth.AUTH_EMAIL_SENDER_EMAIL.split('@')[0], current_app.auth.AUTH_EMAIL_SENDER_EMAIL.split('@')[1])
	msg['To'] = Address(receiver[0], receiver[1].split('@')[0], receiver[1].split('@')[1])
	if replyr:
		msg['Reply-To'] = replyr
	msg.set_content(plain_text)
	if html_text:
		msg.add_alternative(html_text, subtype='html')
	server = smtplib.SMTP(current_app.auth.AUTH_EMAIL_SENDER_SMTP, 587)
	try:
		server.ehlo()
		server.starttls()
		server.ehlo()
		server.login(current_app.auth.AUTH_EMAIL_SENDER_EMAIL, current_app.auth.AUTH_EMAIL_SENDER_PASSWORD)
		server.send_message(msg)
		server.quit()
		return None
	except Exception as e:
		current_app.logger.error("failed to send mail: "+str(e))
		return render_template('auth/email/error.html')