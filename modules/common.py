#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import traceback
import time
from email.header import decode_header
import email
import email.parser
import os


def file_to_lowered_list(filename):
    mlist = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            lowered = line.strip().lower()
            if lowered != '':
                mlist.append(lowered)
    return mlist


def handle_error_update_checkpoint(uid, e="", logger=logging.getLogger('common.py'), send_mail=True):
    from modules.monitor import update_checkpoint
    errlog = str(e) + '\n' + traceback.format_exc()
    logger.error("handle_error_update_checkpoint: " + errlog)
    if uid is not None:
        # Update checkpoint file that mails before this uid is handled successfully
        update_checkpoint('UID updated    :', str(int(uid) - 1))
    logger.info("Checkpoint updated in handle_error_update_checkpoint.")


def update_health_record(health_record_file):
    with open(health_record_file, 'a', encoding='utf-8') as f:
        cur_time = time.strftime('%c', time.localtime(time.time()))
        f.write(cur_time + '\t' + 'Program exits without an error.\n')


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
        subject, encoding_sub = decode_header(raw_subject)[0]
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

class HandledError(Exception):
    def __str__(self):
        return "Handled exception"
