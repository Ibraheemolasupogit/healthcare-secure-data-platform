"""Central logging setup that avoids sensitive context."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure concise process-wide logging."""
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
