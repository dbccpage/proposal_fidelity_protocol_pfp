"""Adversary swarm entrypoints. AuthorityEffect: None."""


def main(argv=None):
    """Load the CLI lazily so python -m executes it exactly once."""
    from .cli import main as cli_main

    return cli_main(argv)


__all__ = ["main"]
