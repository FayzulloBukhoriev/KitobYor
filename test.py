"""Local preview entry point: python test.py runserver [--port 8001]."""
import sys
import subprocess
import run_demo

if __name__=='__main__':
    if len(sys.argv)<2 or sys.argv[1]!='runserver':
        raise SystemExit('Usage: python test.py runserver [--port 8001] [--postgres] [--setup-only]')
    try:run_demo.main(sys.argv[2:])
    except KeyboardInterrupt:print('\nKitobYor stopped. Data is preserved.')
    except subprocess.CalledProcessError as exc:raise SystemExit(f'Command failed ({exc.returncode}). Read the error above. Your database was not deleted.')
