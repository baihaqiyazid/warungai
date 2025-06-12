import logging
from pathlib import Path


def setup_logger(name: str = "transaction_server", log_filename: str = "transaction_server.log", log_dir: str = "logs") -> logging.Logger:
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    log_file = log_path / log_filename

    # Clear existing handlers and configure logging
    logging.getLogger().handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8", mode="a"),
            logging.StreamHandler()
        ],
        force=True
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # logger.info("=== Logger Initialized ===")
    # logger.info(f"Log file path: {log_file.absolute()}")
    return logger
