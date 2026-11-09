import logging
import sys

from dotenv import load_dotenv

from services.database import init_database
from services.logging_config import configure_logging
from services.memory import load_seen_jobs


logger = logging.getLogger(__name__)
load_dotenv()


def main() -> int:
    configure_logging()
    try:
        db_path = init_database()
        load_seen_jobs()
    except Exception as exc:
        logger.error("Healthcheck failed: %s", exc)
        return 1

    logger.info("Healthcheck ok. database=%s", db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
