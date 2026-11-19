import logging
import re
import sys

class SecretScrubbingFilter(logging.Filter):
    """
    Filter to prevent sensitive data such as API keys and secrets
    from ever appearing in application logs.
    """
    PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
        re.compile(r"Bearer\s+[a-zA-Z0-9._-]+", re.IGNORECASE),
        re.compile(r"(api[_-]?key|secret|password)[\"']?\s*[:=]\s*[\"']?([^\"'\s,]+)", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.scrub(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.scrub(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.scrub(str(v)) for v in record.args)
        return True

    def scrub(self, text: str) -> str:
        scrubbed = text
        for pattern in self.PATTERNS:
            scrubbed = pattern.sub("[REDACTED_SECRET]", scrubbed)
        return scrubbed

def setup_logging():
    logger = logging.getLogger("ai_clipper")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretScrubbingFilter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
