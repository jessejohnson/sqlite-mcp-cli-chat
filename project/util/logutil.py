import logging
from settings import settings

is_configured = False
LOG_FILE = settings.LOG_DIR + "mcp_client.log"

def get_log_level() -> str:
    return settings.LOG_LEVEL.upper()

class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_color = Colors.WHITE  # Default color
        
        if record.levelno == logging.DEBUG:
            log_color = Colors.CYAN
        elif record.levelno == logging.INFO:
            log_color = Colors.GREEN
        elif record.levelno == logging.WARNING:
            log_color = Colors.YELLOW
        elif record.levelno == logging.ERROR:
            log_color = Colors.RED
        elif record.levelno == logging.CRITICAL:
            log_color = Colors.MAGENTA

        # Format the log record
        formatted_message = super().format(record)
        return f"{log_color}{formatted_message}{Colors.RESET}"

def setup_logging():
    logger = logging.getLogger()
    formatter = ColoredFormatter('%(asctime)s %(levelname)s>    %(filename)s:line %(lineno)d %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
        )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.setLevel(get_log_level())

    is_configured = True
    logging.info("Loggging set up completed")

def setup_basic_logging():
    logging.basicConfig(
        level=get_log_level(),
        format='%(asctime)s %(levelname)s>    %(filename)s:line %(lineno)d %(message)s',       
         handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )