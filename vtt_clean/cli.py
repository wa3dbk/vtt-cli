from __future__ import annotations
import click

@click.group()
@click.version_option()
def main() -> None:
    """vtt-clean: VTT cleaning and text extraction for ASR corpora."""

# Subcommands registered in later tasks.
