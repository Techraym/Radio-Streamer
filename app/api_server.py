#!/usr/bin/env python3
from __future__ import annotations

import uvicorn
from common import load_config


def main() -> None:
    config = load_config()
    api = config.get("api", {})
    uvicorn.run("api:app", host=str(api.get("bind", "0.0.0.0")), port=int(api.get("port", 8042)), workers=1, access_log=True)


if __name__ == "__main__":
    main()
