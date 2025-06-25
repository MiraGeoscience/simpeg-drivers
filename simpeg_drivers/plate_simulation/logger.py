# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import logging


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with a timestamped stream and speciified log level.

    :param name: Name of the logger.
    :param level: Log level
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.propagate = False

    return logger
