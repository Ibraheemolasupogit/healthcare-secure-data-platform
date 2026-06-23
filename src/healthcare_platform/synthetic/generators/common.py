"""Deterministic date and formatting helpers."""

import random
from datetime import UTC, date, datetime, time, timedelta


def iso_date(value: date) -> str:
    return value.isoformat()


def iso_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def at_utc(value: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime.combine(value, time(hour, minute), tzinfo=UTC)


def random_date(rng: random.Random, start: date, end: date) -> date:
    if end < start:
        return start
    return start + timedelta(days=rng.randint(0, (end - start).days))
