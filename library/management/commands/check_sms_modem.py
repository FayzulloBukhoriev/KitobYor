from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from library.sms.modem import GsmModem,ModemError
from .send_sms import worker_lock

class Command(BaseCommand):
    help='Check modem/SIM/network without sending any SMS.'
    def handle(self,*args,**opts):
        try:
            with worker_lock(settings.SMS_LOCK_FILE):
                with GsmModem(settings.SMS_MODEM_PORT,settings.SMS_MODEM_BAUDRATE,settings.SMS_MODEM_TIMEOUT):pass
        except ModemError as exc:raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS('Modem, SIM and network ready. No SMS sent.'))
