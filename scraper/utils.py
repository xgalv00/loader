"""
Utility classes
"""

import logging
import traceback

import requests


class LoggingMixin(object):
    """Runtime logging configuration"""

    disable_logging = False
    logger = None

    def set_logger(self, logger=None):
        # logger argument should be result of logging.getLogger(name) call
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            # correct logger was not provided. Continue without logging
            self.disable_logging = True

    def log(self, msg, level=logging.INFO, exc_info=False):
        """
        Routes logging message to logger

        Does nothing if self.logger isn't available or disable_logging is true

        :param msg: str of actual message
        :param level: int logging level
        :param exc_info: bool if exc_info should be logged
        """
        if self.logger and not self.disable_logging:
            self.logger.log(level, msg, exc_info=exc_info)

    def get_class_name(self):
        return self.__class__.__name__


class Url(object):
    """Store all necessary data about url that should be processed"""

    def __init__(self, url, id_to_update=None):
        self.url_string = url
        self.id_to_update = id_to_update
        self.fetched_dicts = []
        self.error = False

    def get_response(self):
        """
        Makes request to url
        :return: dict from response or raises if not successful
        """
        response = requests.get(self.url_string, timeout=10)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def append_fetched_dicts(self, objs):
        """
        Adds source_url to each object and stores in list for further processing.

        :param objs: dict
        """
        for key in objs.keys():
            obj = objs[key]
            obj.update({'source_url': self.url_string})
            self.fetched_dicts.append(obj)

    # arguments are sys.exc_info() unpacked
    def handle_error(self, logger, exc_type, exc_value, exc_traceback):
        """
        Provide unified way to handle errors from urls
        """
        last_tb_line = traceback.format_exc().splitlines()[-1]
        # exc_info could be set to True, but last tb line printing is enough for now
        if logger is not None:
            logger.log(msg='Url: {}, e_val: {}'.format(self.url_string, last_tb_line), level=logging.ERROR)
        # used for id exclusion from success update
        self.error = True
