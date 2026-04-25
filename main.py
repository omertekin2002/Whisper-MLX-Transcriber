from __future__ import annotations

import argparse
import sys
from pathlib import Path

from transcriber import DEFAULT_MODEL, LANGUAGES, MODELS, download_model, is_model_available, transcribe_audio


def _language_choices() -> list[str]:
    codes = [code for code in LANGUAGES.values() if code]
    labels = [label.lower().replace(" ", "-") for label in LANGUAGES if LANGUAGES[label]]
    return ["auto", *codes, *labels]


def serve_command(args: argparse.Namespace) -> int:
    try:
        from server import run_server
    except ModuleNotFoundError as exc:
        missing = exc.name or "web dependency"
        raise SystemExit(
            f"Missing dependency '{missing}'. Run ./install.sh or install requirements.txt first."
        ) from exc

    run_server(host=args.host, port=args.port, open_browser=not args.no_open)
    return 0


def transcribe_command(args: argparse.Namespace) -> int:
    text = transcribe_audio(
        audio_path=Path(args.audio),
        model_name=args.model,
        language=args.language,
        download_if_missing=not args.no_download,
    )

    if args.output:
        output = Path(args.output).expanduser()
        output.write_text(text, encoding="utf-8")
        print(f"Wrote transcript to {output}")
    else:
        print(text)
    return 0


def download_model_command(args: argparse.Namespace) -> int:
    download_model(args.model)
    return 0


def models_command(_: argparse.Namespace) -> int:
    longest = max(len(name) for name in MODELS)
    for name, repo in MODELS.items():
        status = "downloaded" if is_model_available(name) else "missing"
        default = " default" if name == DEFAULT_MODEL else ""
        print(f"{name:<{longest}}  {status:<10}  {repo}{default}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whisper-transcriber",
        description="Local Whisper MLX transcription server and command line tool.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="start the local web interface")
    serve.add_argument("--host", default="127.0.0.1", help="server host")
    serve.add_argument("--port", type=int, default=8765, help="server port")
    serve.add_argument("--no-open", action="store_true", help="do not open a browser automatically")
    serve.set_defaults(func=serve_command)

    transcribe = subparsers.add_parser("transcribe", help="transcribe one audio file from the terminal")
    transcribe.add_argument("audio", help="audio file to transcribe")
    transcribe.add_argument("-m", "--model", default=DEFAULT_MODEL, choices=sorted(MODELS), help="Whisper MLX model")
    transcribe.add_argument(
        "-l",
        "--language",
        default="auto",
        choices=_language_choices(),
        help="language code or label; use auto to detect",
    )
    transcribe.add_argument("-o", "--output", help="write transcript to this text file")
    transcribe.add_argument("--no-download", action="store_true", help="fail if the selected model is missing")
    transcribe.set_defaults(func=transcribe_command)

    download = subparsers.add_parser("download-model", help="download a Whisper MLX model")
    download.add_argument("model", nargs="?", default=DEFAULT_MODEL, choices=sorted(MODELS))
    download.set_defaults(func=download_model_command)

    models = subparsers.add_parser("models", help="list configured models and local availability")
    models.set_defaults(func=models_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list:
        args_list = ["serve"]
    elif args_list[0].startswith("-") and args_list[0] not in {"-h", "--help"}:
        args_list = ["serve", *args_list]

    parser = build_parser()
    args = parser.parse_args(args_list)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
