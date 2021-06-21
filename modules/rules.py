import logging
import re


class Rule:
    def __init__(self, params, log_path):
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s: %(name)s: %(levelname)s: %(message)s",
                            filename=log_path,
                            filemode='a')
        self.logger = logging.getLogger('Rules')

        self.subject = params['subject']
        self.content = params['content']
        self.target_keywords = params['target_keywords']

    def get_result(self):
        if any(word in self.content for word in self.target_keywords):
            return {'send_alert': True}
        return {'send_alert': False}