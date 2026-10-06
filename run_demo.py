"""Cross-platform local launcher. Run: python run_demo.py (Python 3.11+)."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parent

def main(argv=None):
    parser=argparse.ArgumentParser(description='KitobYor local preview, no Docker required.')
    parser.add_argument('--postgres',action='store_true',help='Use PostgreSQL configured in .env instead of local SQLite preview.')
    parser.add_argument('--setup-only',action='store_true',help='Prepare database and demo without starting server.')
    parser.add_argument('--port',type=int,default=8000)
    opts=parser.parse_args(argv)
    if sys.version_info<(3,11):raise SystemExit('Python 3.11+ required. Recommended: Python 3.12.')
    os.chdir(ROOT)
    env_dir=ROOT/'.venv';python=env_dir/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():
        print('Creating Python environment...',flush=True);venv.EnvBuilder(with_pip=True).create(env_dir)
    requirements=ROOT/'requirements.txt';digest=hashlib.sha256(requirements.read_bytes()).hexdigest();stamp=env_dir/'.kitobyor-requirements'
    if not stamp.exists() or stamp.read_text()!=digest:
        subprocess.run([str(python),'-m','pip','install','-r',str(requirements)],check=True)
        stamp.write_text(digest)
    env=os.environ.copy();env['DJANGO_SETTINGS_MODULE']='config.settings' if opts.postgres else 'config.demo_settings'
    if opts.postgres:
        env.setdefault('DJANGO_DEBUG','1')
        print('PostgreSQL mode: database must already exist; configuration is read from .env.',flush=True)
    else:print('LOCAL PREVIEW: SQLite demo database. Normal deployment uses PostgreSQL.',flush=True)
    def manage(*args):subprocess.run([str(python),'manage.py',*args],env=env,check=True)
    manage('migrate','--noinput');manage('seed_demo');manage('check')
    if opts.setup_only:return
    print(f'\nOpen http://127.0.0.1:{opts.port}/login/\nUsername: demo. Password was printed on first setup.\nStop server: Ctrl+C\n',flush=True)
    manage('runserver',f'127.0.0.1:{opts.port}','--noreload')

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nKitobYor stopped. Data is preserved.')
    except subprocess.CalledProcessError as exc:raise SystemExit(f'Command failed ({exc.returncode}). Read the error above; do not delete your database.')
