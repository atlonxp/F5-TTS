import logging.config
import logging.config
import os
from logging import Logger, getLogger
from pathlib import Path

import f5_tts.utils.deep_phonemizer.configs
from third_party.deep_phonemizer.utils.io import read_config

main_dir = os.path.dirname(os.path.abspath(f5_tts.utils.deep_phonemizer.configs.__file__))
config_file_path = Path(main_dir) / 'logging.yaml'
config = read_config(config_file_path)
logging.config.dictConfig(config)


def get_logger(name: str) -> Logger:
    """
    Creates a logger object for a given name.

    Args:
        name (str): Name of the logger.

    Returns:
        Logger: Logger object with given name.
    """

    logger = getLogger(name)
    return logger