import logging


class LoggerGetter:
    inited_logger = None

    def get_app_logger(self):
        if self.inited_logger:
            return self.inited_logger
        logging.basicConfig()
        self.inited_logger = logging.getLogger('natcap_wrapper')
        self.inited_logger.setLevel(logging.DEBUG)
        return self.inited_logger


logger_getter = LoggerGetter()
