"""Optional adapters. Deliberately NOT imported by chunkcite/__init__.py.

The core library stays offline and dependency-free. Import an adapter
only when you opt in, e.g.::

    from chunkcite.adapters.gemini import answer_and_verify
"""

from .gemini import answer_and_verify, build_prompt, parse_claims

__all__ = ["answer_and_verify", "build_prompt", "parse_claims"]
