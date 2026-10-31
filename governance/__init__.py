"""Share the installed governance domain with source-checkout tooling. AuthorityEffect: None."""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
