import logging
from colorlog import ColoredFormatter

# Create a logger
logger = logging.getLogger(__name__)

# Set the logging level
logger.setLevel(logging.DEBUG)

# Create a ColoredFormatter
formatter = ColoredFormatter(
    "%(log_color)s[%(asctime)s%(reset)s - %(log_color)s%(levelname)s]%(reset)s %(blue)s%(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Create a StreamHandler and set the formatter
ch = logging.StreamHandler()
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

def dear_lord_show_me_examples_please():
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

# dear_lord_show_me_examples_please()