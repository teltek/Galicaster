# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/notifycrash
#
# Copyright (c) 2015, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import os, time, socket
from email.mime.text import MIMEText
from threading import Thread
import smtplib

from galicaster.core import context

"""
Plugin that sends an email when there is a recording failed. Limitation: only detects future recordings, 
it doesn't analyze the rectemp folder in order to find any older recordings that have failed.
"""

logger = context.get_logger()
conf = context.get_conf()
repo = context.get_repository()


def init():    

    # Get parameters
    subject = context.get_conf().get('notifycrash', 'mailsubject') or "Recording crashed"
    to = context.get_conf().get('notifycrash', 'mailto')
    default_message = context.get_conf().get('notifycrash', 'mailmessage') or "Recording failed"
      
    mail_user = context.get_conf().get('notifycrash', 'mailuser')
    mail_pass = context.get_conf().get('notifycrash', 'mailpass')
    smtpserver = context.get_conf().get('notifycrash', 'smtpserver')
    smtpport = context.get_conf().get('notifycrash', 'smtpport')

    try:
        if repo.crash_file_exists():
            logger.info("There is a recording crashed, trying to send an email")
                        
            filename = os.path.join(repo.get_rectemp_path(), ".recording_crash")
            create_time = "{}".format(time.ctime(os.path.getctime(filename)))

            subject = " # {} - {} - {} #".format(subject, socket.gethostname(), create_time)
            message = """
            {}

            Crash date : {}
            Hostname   : {}
            """.format(default_message, create_time, socket.gethostname())

            if subject and mail_user and mail_pass and to and smtpserver and smtpport:
                t = Thread(target=send_mail, args=(subject, to, message, mail_user, mail_pass, smtpserver, smtpport))
                t.start()

            else:
                logger.debug("Not sending email due to missing parameters, please introduce 'mailuser', 'mailpass', 'to', 'smtpserver' and 'smtpport' in section 'notifycrash' of the config file")
                    
        else:
            logger.debug("Nothing to do (does not exist '.recording_crash' file)")

    except Exception as exc:
        logger.error("Error sending the email: {}".format(exc))

    return True
    
        
def send_mail(subject=None, to=None, message=None, mail_user=None, mail_pass=None, server_smtp=None, server_port=None):
    logger.debug("Trying to send email to {}, subject:{}".format(to, subject))

    try:
        msg = MIMEText(message)
        
        msg['Subject'] = subject
        msg['From'] = mail_user
        msg['To'] = to
        
        # Auth
        mailServer = smtplib.SMTP(server_smtp , server_port)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        
        # Init connection
        mailServer.login(mail_user,mail_pass)
        
        # Send email
        mailServer.sendmail(mail_user, to, msg.as_string())
        
        # Close connection
        mailServer.close()
        
        logger.info("Email sent  to {}, subject:{}. So removing crash file...".format(to, subject))
        repo.crash_file_remove()
        logger.debug("Crash file removed")
        
    except Exception as exc:
        logger.error("There was an error sending the email: {}".format(exc))
    
    return True
                

