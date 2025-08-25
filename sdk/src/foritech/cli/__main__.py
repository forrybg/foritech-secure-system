import sys
import importlib

def _run():
    pkg = importlib.import_module("foritech.cli")
    fn = getattr(pkg, "main", None)
    if callable(fn):
        return fn()
    # fallback: ако някой е изтрил main(), покажи смислено съобщение
    sys.stderr.write("foritech.cli: missing callable main() in package; cannot run as module.\n")
    return 2

if __name__ == "__main__":
    raise SystemExit(_run())
