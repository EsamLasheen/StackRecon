"""Writer — atomically writes scan results to a JSON file."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def write_atomic(data: dict, output_path: str | Path) -> None:
    """Write data as JSON to output_path atomically via a temp file.

    The data is serialized to a temporary file in the same directory as
    output_path, then renamed into place. On failure, the original file
    (if any) is left completely untouched.

    Args:
        data:        JSON-serializable dict to write.
        output_path: Destination path for data.json.

    Raises:
        TypeError:   If data contains non-JSON-serializable values.
        OSError:     If the directory is unwritable or disk is full.
    """
    output_path = Path(output_path)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Serialize first — raises TypeError before touching disk if invalid.
    serialized = json.dumps(data, indent=2, ensure_ascii=False)

    fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(serialized)
        os.replace(tmp_path, output_path)
    except Exception:
        # Clean up temp file; leave original untouched.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
