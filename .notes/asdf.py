import logging

# Configure the logging format
log_format = "%(asctime)s [%(levelname)s]\t%(message)s"
date_format = "%Y-%m-%d_%H:%M:%S"

# Create a logging handler to specify the log format and date format
logging.basicConfig(format=log_format, datefmt=date_format)

# Create a logger instance
logger = logging.getLogger(__name__)

# Set the logging level (you can change this to DEBUG, INFO, WARNING, ERROR, or CRITICAL)
logger.setLevel(logging.INFO)

# Log a message
logger.info("This is an example log message.")
