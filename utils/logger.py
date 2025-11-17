"""Enhanced logging system using loguru."""
import sys
from pathlib import Path
from loguru import logger as _logger


def setup_logger(
    log_file: str = "logs/redbot.log",
    rotation: str = "10 MB",
    retention: str = "30 days",
    compression: str = "zip",
    level: str = "INFO"
):
    """Setup logger with rotation and retention.

    Args:
        log_file: Path to log file
        rotation: When to rotate logs (size or time)
        retention: How long to keep old logs
        compression: Compression format for old logs
        level: Minimum log level
    """
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    _logger.remove()

    # Add console handler with colors
    _logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # Add file handler with rotation
    _logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        backtrace=True,
        diagnose=True,
    )

    return _logger


# Create default logger instance
logger = setup_logger()


# Convenience functions for structured logging
def log_with_context(level: str, message: str, **context):
    """Log message with additional context.

    Args:
        level: Log level (info, warning, error, debug)
        message: Log message
        **context: Additional context fields
    """
    log_method = getattr(logger, level.lower())
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        log_method(f"{message} | {context_str}")
    else:
        log_method(message)


def log_job_found(job_url: str, source: str, score: int = 0):
    """Log when a new job is found.

    Args:
        job_url: Job URL
        source: Source (reddit, hackernews, etc.)
        score: Priority score
    """
    log_with_context(
        "info",
        "Job found",
        source=source,
        url=job_url,
        score=score
    )


def log_api_call(source: str, endpoint: str, duration_ms: int, success: bool = True):
    """Log API call with metrics.

    Args:
        source: API source
        endpoint: API endpoint
        duration_ms: Request duration in milliseconds
        success: Whether request succeeded
    """
    level = "info" if success else "error"
    log_with_context(
        level,
        "API call",
        source=source,
        endpoint=endpoint,
        duration_ms=duration_ms,
        success=success
    )


def log_error_with_traceback(message: str, exception: Exception):
    """Log error with full traceback.

    Args:
        message: Error message
        exception: Exception object
    """
    logger.exception(f"{message}: {str(exception)}")
