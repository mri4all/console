import logging, sys, os, re

import common.runtime as rt

logger_setup_complete = False
logger = None

def get_logger():
    """Returns an instance of the logger service."""
    global logger_setup_complete
    global logger

    if not logger_setup_complete:
        logger = logging.getLogger(rt.service_name)
        logger_setup_complete = True
        logger.setLevel(get_loglevel())

        # Create console handler
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger
    return logger    


def get_loglevel() -> int:
    """Returns the logging level that should be used for printing messages."""
    if any(re.findall(r"pytest|py.test", sys.argv[0])):
        return logging.DEBUG

    level = os.getenv("MRI4ALL_LOG_LEVEL", "info").lower()
    if level == "error":
        return logging.ERROR
    if level == "info":
        return logging.INFO
    if level == "debug":
        return logging.DEBUG

    return logging.INFO

