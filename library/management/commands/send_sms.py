"""Single worker per modem. No auto-send in local demo mode."""
import os
import time
from pathlib import Path
from contextlib import contextmanager
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import close_old_connections
from library.sms.worker import process_one,recover_stale

@contextmanager
def worker_lock(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as f:
        try:
            if os.name=='nt':
                import msvcrt
                if f.seek(0,2)==0:f.write(b'0');f.flush()
                f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise CommandError('SMS worker аллакай кор мекунад.') from exc
        try:yield
        finally:
            if os.name=='nt':f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f,fcntl.LOCK_UN)

class Command(BaseCommand):
    help='Send queued SMS through a local GSM modem/SIM (no provider API).'
    def add_arguments(self,parser):
        parser.add_argument('--once',action='store_true',help='Process one message and exit.')
    def handle(self,*args,**opts):
        if settings.SMS_BACKEND!='gsm' or settings.DEMO_MODE:raise CommandError('Барои фиристодан SMS_BACKEND=gsm ва муҳити воқеӣ лозим аст. Demo SMS намефиристад.')
        if not settings.SMS_MODEM_PORT:raise CommandError('SMS_MODEM_PORT-ро танзим кунед.')
        try:
            with worker_lock(settings.SMS_LOCK_FILE):
                recover_stale()
                while True:
                    close_old_connections();sms=process_one()
                    if sms:self.stdout.write(f'SMS #{sms.pk}: {sms.status}')
                    if opts['once']:break
                    time.sleep(2 if sms else 5)
        except KeyboardInterrupt:self.stdout.write('SMS worker stopped.')
