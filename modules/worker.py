#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import email
import email.parser
import json
import logging
import smtplib
import ssl
import sys
import requests
from modules.configreader import conf
from modules.common import handle_error_update_checkpoint, HandledError


class Worker:
    def __init__(self):
        self.logger = logging.getLogger('Worker')
        # python 3.6 or earlier version: PROTOCOL_SSLv23, later version: PROTOCOL_TLS
        if sys.version_info[1] < 6:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.smtp = smtplib.SMTP(host=conf.smtp_server,
                                 port=conf.smtp_port)
        self.smtp.ehlo()
        self.smtp.starttls(context=context)
        self.smtp.ehlo()
        try:
            self.smtp.login(conf.smtp_account, conf.smtp_password)
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error("Cannot login to STMP server: %s" % str(e))
            exit()

    def close_connection(self):
        try:
            self.smtp.quit()
        except smtplib.SMTPServerDisconnected:
            self.logger.info("close_connection: already disconnected.")
            pass

    def send_alert(self, subject=None, content=None, content_type='plain',
                   receivers=None, sender=None, smtp_close=False, uid=None):
        alert = email.message.EmailMessage()
        if receivers is None:
            try:
                receivers = conf.receivers
            except Exception as err:
                self.logger.info(err)
                receivers = []

        alert['Subject'] = subject.replace('\n', '').replace('\r', '')  # Error when \n or \r is contained
        alert.set_content(content, subtype=content_type)
        alert['From'] = sender
        alert['To'] = receivers

        try:
            self.smtp.send_message(alert)
        except Exception as e:
            self.logger.info("send_message exception. %s." % str(e))
            handle_error_update_checkpoint(uid=uid, e=e, logger=self.logger)
            raise HandledError

        if smtp_close:
            self.close_connection()

    def create_issue(self, subject, content):
        data = {'title': subject, 'body': content}
        post_url = conf.github_issue_url

        r = requests.post(url=post_url, data=json.dumps(data))
        if r.status_code != 201:
            raise Exception
        return r
