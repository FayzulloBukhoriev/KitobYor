from datetime import timedelta
from django.conf import settings
from django.db import transaction,connection
from django.db.models import Q
from django.utils import timezone
from library.models import SmsNotification,SmsPart
from .modem import GsmModem,ModemError,SubmissionUncertain

@transaction.atomic
def claim():
    qs=SmsNotification.objects.filter(status__in=['queued','retry'],next_attempt_at__lte=timezone.now()).exclude(invoice__school__code='DEMO').order_by('id')
    qs=qs.select_for_update(skip_locked=True) if connection.features.has_select_for_update_skip_locked else qs.select_for_update()
    sms=qs.first()
    if sms:
        sms.status='processing';sms.locked_at=timezone.now();sms.attempts+=1
        sms.save(update_fields=['status','locked_at','attempts'])
    return sms

@transaction.atomic
def recover_stale():
    # Only called while holding the single worker/modem OS lock.
    for sms in SmsNotification.objects.select_for_update().filter(status='processing'):
        if sms.parts.exists() and not sms.parts.exclude(status='submitted').exists():
            sms.status='submitted';sms.sent_at=sms.parts.order_by('-submitted_at').first().submitted_at
            sms.locked_at=None;sms.last_error='';sms.provider_reference=','.join(sms.parts.values_list('reference',flat=True))[:160];sms.save()
            continue
        uncertain=sms.parts.filter(status__in=['submitting','uncertain']).exists()
        sms.parts.filter(status='submitting').update(status='uncertain')
        sms.status='uncertain' if uncertain else ('retry' if sms.attempts<settings.SMS_MAX_ATTEMPTS else 'failed')
        sms.last_error='Worker қатъ шуда буд; натиҷаи қисми фиристодашуда санҷиш мехоҳад.' if uncertain else 'Worker пеш аз фиристодан қатъ шуд.'
        sms.next_attempt_at=timezone.now();sms.locked_at=None;sms.save()

def process_one(modem_factory=GsmModem):
    if settings.SMS_BACKEND!='gsm' or settings.DEMO_MODE:return None
    sms=claim()
    if not sms:return None
    try:
        if sms.parts.filter(status__in=['submitting','uncertain']).exists():raise SubmissionUncertain('Натиҷаи пешина номаълум аст.')
        with modem_factory(settings.SMS_MODEM_PORT,settings.SMS_MODEM_BAUDRATE,settings.SMS_MODEM_TIMEOUT) as modem:
            for part in sms.parts.filter(status='pending').order_by('sequence'):
                def before_submit(pk=part.pk):
                    SmsPart.objects.filter(pk=pk,status='pending').update(status='submitting')
                reference=modem.submit(part,before_submit)
                SmsPart.objects.filter(pk=part.pk).update(status='submitted',reference=reference,submitted_at=timezone.now())
        if not sms.parts.exists() or sms.parts.exclude(status='submitted').exists():raise SubmissionUncertain('Ҳамаи қисмҳои SMS тасдиқ нашуданд.')
        sms.status='submitted';sms.sent_at=timezone.now()
        sms.provider_reference=','.join(sms.parts.values_list('reference',flat=True))[:160];sms.last_error=''
    except SubmissionUncertain as exc:
        sms.parts.filter(status='submitting').update(status='uncertain')
        sms.status='uncertain';sms.last_error=str(exc)[:250]
    except ModemError as exc:
        sms.status='retry' if sms.attempts<settings.SMS_MAX_ATTEMPTS else 'failed'
        sms.next_attempt_at=timezone.now()+timedelta(seconds=min(60*5**(sms.attempts-1),3600))
        sms.last_error=str(exc)[:250]
    except Exception:
        # Unknown failure after touching hardware is not safe to retry blindly.
        sms.parts.filter(status='submitting').update(status='uncertain')
        sms.status='uncertain';sms.last_error='Хатои ғайричашмдошт; санҷиши масъул лозим аст.'
    sms.locked_at=None;sms.save()
    return sms
