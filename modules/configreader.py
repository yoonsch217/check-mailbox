#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import datetime
import logging
import os
import time
import configparser
from optparse import OptionParser
import socket


cur_time = datetime.datetime.now()
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
configlogger = logging.getLogger('configreader')


class ConfigReader:
    def __init__(self, configfiles):
        self.logger = logging.getLogger('ConfigReader')
        self.config = configparser.RawConfigParser()
        self.config.read(configfiles, encoding='utf-8')

        current_year = time.localtime(time.time()).tm_year
        current_month = time.localtime(time.time()).tm_mon
        current_day = time.localtime(time.time()).tm_mday
        mtoday = datetime.datetime(current_year, current_month, current_day)
        server_date_affix = socket.gethostname() + '-' + str(mtoday)[:10]

        self.imap_server = self.config.get('mail', 'imap_server')
        self.imap_port = self.config.get('mail', 'imap_port')
        self.imap_account = self.config.get('mail', 'imap_account')
        self.imap_password = self.config.get('mail', 'imap_password')

        self.smtp_server = self.config.get('mail', 'smtp_server')
        self.smtp_port = self.config.get('mail', 'smtp_port')
        self.smtp_account = self.config.get('mail', 'smtp_account')
        self.smtp_password = self.config.get('mail', 'smtp_password')

        self.logfile = base_dir + '/logs/' + server_date_affix + '-' + self.config.get('file', 'log_file')
        self.checkpoint_file = base_dir + '/' + self.config.get('file', 'checkpoint_file')
        self.health_record_file = base_dir + '/health-records/' + server_date_affix + '-' + self.config.get('file', 'health_record_file')

        self.github_issue_url = self.config.get('url', 'github_api_url') + '/issues'
        self.master_keywords_file = base_dir + '/files/' + self.config.get('file', 'master_keywords_file')

        self.receivers = [self.config.get('file', 'receiver_addresss')]
        self.sender = self.config.get('file', 'sender_address')

        # Setup directories
        if not os.path.exists(os.path.dirname(self.logfile)):
            os.mkdir(os.path.dirname(self.logfile))
        if not os.path.exists(os.path.dirname(self.checkpoint_file)):
            os.mkdir(os.path.dirname(self.checkpoint_file))
        if not os.path.exists(os.path.dirname(self.health_record_file)):
            os.mkdir(os.path.dirname(self.health_record_file))


parser = OptionParser()
parser.add_option('-c', '--config',
                  default=base_dir + '/config/config.ini',
                  help='Path to config file (default: %default)',
                  metavar='FILE')

(options, args) = parser.parse_args()
config = configparser.RawConfigParser()
config.read(options.config, encoding='utf-8')


# logging
local_time = time.localtime(time.time())
today = datetime.datetime(local_time.tm_year, local_time.tm_mon, local_time.tm_mday)
logfile = base_dir + '/logs/' + socket.gethostname() + '-' + str(today)[:10] + '-' + config.get('file', 'log_file')
logging.basicConfig(level=logging.DEBUG,
                    format=socket.gethostname()+" %(asctime)s: %(name)s: %(levelname)s: %(message)s",
                    filename=logfile,
                    filemode='a')

consolelog = logging.StreamHandler()
consolelog.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
logging.getLogger('').addHandler(consolelog)


conf = ConfigReader(configfiles=[options.config])

