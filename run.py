#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import traceback
import imaplib
import time
import logging
from modules.monitor import Monitor
from modules.configreader import conf
from modules.common import update_health_record


def main():
    logmain = logging.getLogger('Main')
    monitor = Monitor()
    while True:
        try:
            monitor.run_once()
            break
        except imaplib.IMAP4.abort as err:
            logmain.warning("Server error: %s \nreconnecting in 30 seconds..." % err)
            time.sleep(30)
            monitor.__init__()
        except KeyboardInterrupt:
            # Ctrl-c
            logmain.info('Received ctrl-c or SIGINT, cleaning up')
            monitor.disconnect()
            sys.exit(0)


if __name__ == "__main__":
    logger = logging.getLogger('Run')
    try:
        main()
        update_health_record(conf.health_record_file)

    except KeyboardInterrupt as e:
        # Ctrl-c
        logger.error(e)
        logger.debug('Exit\n ')
        raise e
    except Exception as e:
        logger.error("ERROR, UNEXPECTED EXCEPTION")
        errlog = str(e) + '\n' + traceback.format_exc()
        logger.error(errlog)
        try:
            # Handle unexpected exception
            logger.debug('Exit\n ')
        except:
            logger.debug('Exit\n ')
