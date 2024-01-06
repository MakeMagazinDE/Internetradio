import logging

logger = logging.getLogger(__name__)

def get_rolling_text(text, current_pos):
    logger.debug("get_rolling_text")
    if len(text) <= 20:
        return text, 0

    if current_pos > len(text)-20:
        current_pos = 0

    rolling_text = text[current_pos:current_pos+20]
    current_pos += 1
    return rolling_text, current_pos
