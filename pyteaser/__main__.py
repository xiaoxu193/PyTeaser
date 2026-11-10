"""Allow running the PyTeaser CLI as ``python -m pyteaser``."""

from pyteaser import main

if __name__ == "__main__":
    raise SystemExit(main())
