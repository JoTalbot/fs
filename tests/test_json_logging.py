import io
import json
import logging

import pytest

from fs_overlay.json_logging import JsonLogFormatter, configure_json_logging, log_event


def test_json_formatter_emits_structured_fields_deterministically():
    record = logging.LogRecord("fs_overlay", logging.INFO, __file__, 1, "stored", (), None)
    record.fs_fields = {"node": "n1", "objects": 2}

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload == {
        "fields": {"node": "n1", "objects": 2},
        "level": "INFO",
        "logger": "fs_overlay",
        "message": "stored",
    }


def test_log_event_keeps_fields_out_of_message():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = configure_json_logging(logging.getLogger("fs_overlay.test"), handler=handler)
    try:
        log_event(logger, logging.INFO, "snapshot created", snapshot_id="s1", generation=3)
        payload = json.loads(stream.getvalue())
    finally:
        logger.removeHandler(handler)

    assert payload["message"] == "snapshot created"
    assert payload["fields"] == {"generation": 3, "snapshot_id": "s1"}


def test_formatter_rejects_non_mapping_fields():
    record = logging.LogRecord("fs_overlay", logging.INFO, __file__, 1, "bad", (), None)
    record.fs_fields = ["not", "a", "mapping"]

    with pytest.raises(TypeError, match="fs_fields"):
        JsonLogFormatter().format(record)
