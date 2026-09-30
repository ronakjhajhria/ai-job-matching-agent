import logging
import sys

def configure_logging(level: str = "INFO") -> None:
    """Configure standard-library logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # Silence overly verbose third-party loggers if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)
