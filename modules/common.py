#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import traceback
import time


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
    errlog = str(e) + '\n' + traceback.format_exc()
    logger.error("handle_error_update_checkpoint: " + errlog)
    if uid is not None:
        from modules.monitor import Monitor
        # Update checkpoint file that mails before this uid is handled successfully
        Monitor().update_checkpoint('UID updated    :', str(int(uid) - 1))
    logger.info("Checkpoint updated in handle_error_update_checkpoint.")


def update_health_record(health_record_file):
    with open(health_record_file, 'a', encoding='utf-8') as f:
        cur_time = time.strftime('%c', time.localtime(time.time()))
        f.write(cur_time + '\t' + 'Program exits without an error.\n')


class HandledError(Exception):
    def __str__(self):
        return "Handled exception"
