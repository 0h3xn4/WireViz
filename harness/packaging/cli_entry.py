"""PyInstaller entry point for the console command `harness` (validate, check, migrate)."""

from harness_tool.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
