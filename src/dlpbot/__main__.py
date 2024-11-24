from __future__ import annotations

import argparse
import asyncio
import contextlib
import os

import dlpbot.client
import dlpbot.log


def _main():
    parser = argparse.ArgumentParser(dlpbot.__name__)
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=dlpbot.__version__,
        help="discord token to use (or TOKEN env variable)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable verbose logging",
    )
    parser.add_argument(
        "--token",
        help="discord token to use (or TOKEN env var)",
    )
    parser.add_argument(
        "channel",
        nargs="+",
        help="channel ids to monitor",
    )
    args = parser.parse_args()

    if not args.token:
        args.token = os.getenv("TOKEN")
        if not args.token:
            parser.error("neither --token nor the TOKEN env var were supplied")

    dlpbot.log.setup(debug=args.verbose)
    client = dlpbot.client.Client(args.channel)
    asyncio.run(client.start(args.token))


def main():
    with contextlib.suppress(KeyboardInterrupt):
        _main()


if __name__ == "__main__":
    main()
