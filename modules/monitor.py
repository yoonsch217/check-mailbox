#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import email
import email.parser
import imaplib
import logging
import os
import sys
import time
import traceback
from email.header import decode_header
import socket
import threading

from modules import rules
from modules.worker import Worker
from modules.common import file_to_lowered_list, handle_error_update_checkpoint, HandledError
from modules.configreader import conf


def decode_email(raw_email):
    msg = email.message_from_bytes(raw_email)
    content = ''
    content_type = None

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == 'text':
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    payload = payload.decode()
                content = payload
                content_type = part.get_content_subtype()
    else:
        if msg.get_content_maintype() == 'text':
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                payload = payload.decode()
            content = payload
            content_type = msg.get_content_subtype()

    raw_subject = msg.get('Subject')
    subject = ''
    if raw_subject is not None:
        # Header values may not contain linefeed or carriage return characters
        subject, encoding_sub = decode_header(raw_subject)
        if encoding_sub is not None:
            subject = subject.decode(encoding_sub)
        elif type(subject) is not str:
            subject = subject.decode()
        if isinstance(subject, str):
            subject = subject.replace('\n', '').replace('\r', '')
    else:
        logging.error("Subject is None.")
        subject = "None"

    if msg.get('From') is not None:
        mail_from_list = []
        for raw_from in decode_header(msg.get('From')):
            mail_from, encoding_from = raw_from
            if encoding_from is not None:
                mail_from_list.append(mail_from.decode(encoding_from))
            elif isinstance(mail_from, bytes):
                mail_from_list.append(mail_from.decode())
            else:
                mail_from_list.append(mail_from)
        mail_from = ' '.join(mail_from_list)
    else:
        mail_from = None
    logging.debug("Mail from: %s" % mail_from)

    return {'subject': str(subject), 'content': content,
            'content_type': content_type, 'mail_from': str(mail_from)}


def exit_process(uid):
    logging.error("exit_process(): Timeout Error: Process aborted for timeout. %s" % str(uid))
    handle_error_update_checkpoint(uid=uid.decode(), e="", logger=logging, send_mail=False)
    os._exit(1)


class Monitor:
    def __init__(self):
        self.logger = logging.getLogger('Monitor')
        self.mail = imaplib.IMAP4_SSL(host=conf.imap_server, port=conf.imap_port)
        try:
            self.mail.login(conf.imap_account, conf.imap_password)
        except imaplib.IMAP4.error as e:
            self.logger.error("Cannot login to STMP server: %s" % str(e))
            exit()

    def _handle_error(self, error_msg=None):
        self.logger.critical(error_msg + '\n' + traceback.format_exc())
        self.disconnect()
        sys.exit(1)

    def disconnect(self):
        self.logger.info('Logging out')
        self.mail.logout()

    # Reading checkpoint file
    def get_latest_uid(self):
        if os.path.isfile(conf.shared_checkpoint_file):
            last_seen = self.parse_checkpoint_or_none(conf.shared_checkpoint_file)
            if not last_seen:
                last_seen = self.parse_checkpoint_or_none(conf.local_checkpoint_file)
                self.logger.warning("Check checkpoint file.")
            return int(last_seen)
        else:
            self.logger.info("Checkpoint file does not exist.")
            return -1

    def parse_checkpoint_or_none(self, filename):
        last_seen = None
        with open(filename, 'r', encoding='utf-8') as f:
            lines = list(f)
            for i in range(len(lines)-1, -1, -1):
                if len(lines[i].split('\t')) != 4:
                    self.logger.warning("Tab split size is %s." % str(len(lines[i].split('\t'))))
                    continue
                last_seen = lines[i].split('\t')[1]  # uid is at the second index
                if last_seen != '-1' and not last_seen.isdigit():
                    self.logger.warning("Uid is not a digit")
                    continue
                break
            return last_seen

    def update_checkpoint(self, status, uid):
        cur_time = time.strftime('%c', time.localtime(time.time()))
        updating_data = status + '\t' + uid + '\t' + cur_time + '\t' + socket.gethostname() + '\n'
        new_lines = []
        if os.path.isfile(conf.checkpoint_file):
            with open(conf.checkpoint_file, 'r', encoding='utf-8') as f:
                new_lines = f.readlines()
        new_lines.append(updating_data)
        with open(conf.checkpoint_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    def read_single_mail(self, num, worker, target_keywords):
        self.logger.info('===========================Received new email with id ' + str(num) + '===========================')
        typ, rfc = self.mail.uid('fetch', num, '(RFC822)')
        if typ != 'OK':
            self._handle_error('Did not receive ok from server (fetch rfc): %s' % typ)
        raw_email = rfc[0][1]

        decoded_email = decode_email(raw_email)
        subject = decoded_email['subject'].strip()
        content = decoded_email['content']
        content_type = decoded_email['content_type']

        # Checking rules
        params = decoded_email
        params['target_keywords'] = target_keywords
        rule_result = rules.Rule(params, conf.logfile).get_result()

        if rule_result['send_alert']:
            self.handle_target_email(worker=worker, subject=subject, content=content,
                                     content_type=content_type, uid=num.decode())
        else:
            pass
        self.logger.info('uid: ' + str(num) + ' finished.')

    def handle_target_email(self, worker, subject, content, content_type, uid):
        worker.send_alert(subject=subject, content=content, content_type=content_type,
                            receivers=conf.receivers, sender=conf.sender, uid=uid)
        worker.create_issue(subject=subject, content=content)

    def run_once(self):
        res, nums = self.mail.select()  # default=INBOX
        if res != 'OK':
            self.logger.error(nums)
            exit(1)

        last_seen_uid = self.get_latest_uid()
        if last_seen_uid == -1:
            self.logger.info("Reading recent 100 mails.")
            typ, msgnums = self.mail.uid('search', None, 'ALL')
            msgnums = [b' '.join(msgnums[0].split()[-100:])]
        else:
            typ, msgnums = self.mail.uid('search', 'UID %s:*' % str(last_seen_uid + 1))

        target_keywords = file_to_lowered_list(conf.master_keywords_file)
        any_mail = False
        self.logger.info("Mails to parse: %s" % msgnums)

        worker = Worker()
        for num in msgnums[0].split():
            if int(num.decode()) <= last_seen_uid:
                self.logger.info("No mail to parse. Already seen.")
                break
            any_mail = True
            try:
                # Timeout for each email
                timer = threading.Timer(60, exit_process, [num])
                timer.start()
                self.read_single_mail(num, worker, target_keywords)
                timer.cancel()
            except HandledError:
                break
            except Exception as e:
                errlog = str(e) + '\n' + traceback.format_exc()
                self.logger.error(errlog)
                handle_error_update_checkpoint(uid=num.decode(), e=errlog, logger=self.logger)
                break

        worker.close_connection()

        if any_mail:
            self.update_checkpoint('UID updated    :', msgnums[0].split()[-1].decode())
        else:
            self.update_checkpoint('UID not updated:', str(last_seen_uid))
