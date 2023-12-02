import logging, sys, os, re
from logging.handlers import RotatingFileHandler

import common.runtime as rt

# Global logger instance
logger = None
logger_setup_complete = False


class TaskIDFilter(logging.Filter):
    """
    This is a filter which injects information about the active task ID into the log
    """

    def filter(self, record):
        record.taskID = rt.get_current_task_id()
        return True


def get_logger():
    """Returns an instance of the logger service."""
    global logger_setup_complete
    global logger

    if not logger_setup_complete:
        logger = logging.getLogger(rt.service_name)
        logger_setup_complete = True
        logger.setLevel(get_loglevel())
        logger.addFilter(TaskIDFilter())
        logging.addLevelName(logging.NOTSET, "NOT")
        logging.addLevelName(logging.DEBUG, "DBG")
        logging.addLevelName(logging.INFO, "INF")
        logging.addLevelName(logging.WARNING, "WRN")
        logging.addLevelName(logging.ERROR, "ERR")
        logging.addLevelName(logging.CRITICAL, "CTL")
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(taskID)s | %(message)s"
        )

        # Create console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        file_handler = RotatingFileHandler(
            f"/opt/mri4all/logs/{rt.service_name}.log", maxBytes=1500000, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger
    return logger


def get_loglevel() -> int:
    """Returns the logging level that should be used for printing messages."""
    if any(re.findall(r"pytest|py.test", sys.argv[0])):
        return logging.DEBUG

    level = os.getenv("MRI4ALL_LOG_LEVEL", "info").lower()
    if rt.is_debugging_enabled():
        level = "debug"

    if level == "error":
        return logging.ERROR
    if level == "info":
        return logging.INFO
    if level == "debug":
        return logging.DEBUG

    return logging.INFO


class LoggerStdCapture:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        # The check for empty lines reduces the amount printed to the logger
        if message != "\n":
            self.level(message)

    def flush(self):
        pass
        # self.level(sys.stderr)
