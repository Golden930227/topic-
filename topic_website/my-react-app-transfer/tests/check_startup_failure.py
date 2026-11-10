"""Opt-in integration: inject only monitor startup failure; reuse existing services."""
import subprocess
from pathlib import Path
from urllib.request import urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    source = (root / 'start_all.ps1').read_text(encoding='utf-8-sig')
    source = source.replace('$root = $PSScriptRoot', "$root = '" + str(root).replace("'", "''") + "'")
    original = "& (Join-Path $root 'start_pipeline_monitor.ps1')"
    assert original in source
    source = source.replace(original, "throw 'Injected monitor startup failure (test only)'")
    target = root / '.windmind-logs/startup-failure-check.ps1'
    target.parent.mkdir(exist_ok=True)
    target.write_text(source, encoding='utf-8-sig')
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                 '-File', str(target), '-NoBrowser'], capture_output=True, timeout=90)
        assert result.returncode == 0, result.stderr
        assert b'Injected monitor startup failure' in result.stdout
        assert b'Other WindMind services are still running' in b' '.join(result.stdout.split())
        for port in (5173, 5174, 5175, 8000):
            path = '/openapi.json' if port == 8000 else '/'
            with urlopen(f'http://127.0.0.1:{port}{path}', timeout=3) as response:
                assert response.status == 200
        print('PASS: monitor failure was isolated; all four existing services returned HTTP 200.')
    finally:
        target.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
