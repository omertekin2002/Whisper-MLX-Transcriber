from __future__ import annotations

import argparse

from transcriber import DEFAULT_MODEL, MODELS, download_model


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Whisper MLX models used by the local transcriber.")
    parser.add_argument("model", nargs="?", default=DEFAULT_MODEL, choices=sorted(MODELS))
    args = parser.parse_args()

    path = download_model(args.model)
    print(f"Model ready at {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
