import logging
import requests
from config import PUSHOVER_TOKEN, PUSHOVER_USER

log = logging.getLogger(__name__)


def push(msg):
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        return False

    try:
        r = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": PUSHOVER_TOKEN, "user": PUSHOVER_USER, "message": msg},
            timeout=5,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        log.error("pushover failed: %s", e)
        return False