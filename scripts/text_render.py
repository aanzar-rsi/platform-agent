#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


def clean_rendered_text(text: str) -> str:
    """
    Convert common escaped formatting characters into readable text.

    HTML/XML content is left completely untouched.
    """

    replacements = {
        r"\r\n": "\n",
        r"\n": "\n",
        r"\r": "\n",
        r"\t": "\t",
        r"\"": '"',
        r"\'": "'",
    }

    for encoded, decoded in replacements.items():
        text = text.replace(encoded, decoded)

    # Remove trailing whitespace while preserving indentation
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Render escaped text into a readable format."
    )

    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Read escaped text from a file."
    )

    input_group.add_argument(
        "-t",
        "--text",
        help="Provide escaped text directly."
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write cleaned text to a file instead of stdout."
    )

    args = parser.parse_args()

    if args.file:
        if not args.file.exists():
            parser.error(f"File not found: {args.file}")

        if not args.file.is_file():
            parser.error(f"Not a file: {args.file}")

        raw_text = args.file.read_text(encoding="utf-8")
    else:
        raw_text = args.text

    cleaned_text = clean_rendered_text(raw_text)

    if args.output:
        args.output.write_text(cleaned_text, encoding="utf-8")
        print(f"Output written to: {args.output}")
    else:
        print(cleaned_text)


if __name__ == "__main__":
    main()