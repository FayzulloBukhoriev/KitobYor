"""Transactional SMS outbox; direct GSM worker runs outside the web request."""
import secrets
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import SmsNotification,SmsPart
from .sms.pdu import encode_message

def live_sms_enabled(invoice):
    return settings.SMS_BACKEND=='gsm' and not settings.DEMO_MODE and invoice.school.code!='DEMO'

@transaction.atomic
def prepare_sms(invoice):
    student=invoice.loan.student
    body=(f'{invoice.school.name}: {student.full_name} — иҷораи китобҳо {invoice.total:.2f} сомонӣ. '
          f'Рақами дохилии пардохт: {invoice.payment_number}. '
          'Барои пардохт ба мактаб муроҷиат кунед. Пайвасти бонк ҳоло фаъол нест.')
    notification,created=SmsNotification.objects.get_or_create(invoice=invoice,defaults={'destination':student.parent_phone,'body':body})
    if created:prepare_parts(notification,enabled=live_sms_enabled(invoice))
    return notification

def prepare_parts(notification,enabled):
    if not notification.destination:
        notification.status='missing_phone'
    else:
        try:parts=encode_message(notification.destination,notification.body,secrets.randbelow(65536))
        except (ValueError,ValidationError):
            # Validation errors are isolated from financial transactions. Never fake a send.
            notification.status='failed';notification.last_error='Телефон ё матни SMS нодуруст аст.'
        else:
            SmsPart.objects.bulk_create([SmsPart(notification=notification,sequence=p.sequence,pdu=p.hex,tpdu_length=p.length) for p in parts])
            notification.status='queued' if enabled else 'preview'
            notification.next_attempt_at=timezone.now() if enabled else None
    notification.save()

@transaction.atomic
def requeue_sms(*,user,school,notification_id):
    from . import services
    services.authorize(user,school,['admin','librarian'])
    sms=services.find(SmsNotification.objects.select_for_update().select_related('invoice__loan__student','invoice__school').filter(invoice__school=school),notification_id)
    if sms.status not in ('preview','missing_phone','failed'):raise services.DomainError('Ин паём аллакай дар навбат ё фиристода шудааст.')
    if sms.parts.exclude(status='pending').exists():raise services.DomainError('Паём қисман фиристода шудааст; санҷиши масъул лозим аст.')
    sms.parts.all().delete()
    sms.destination=sms.invoice.loan.student.parent_phone
    sms.attempts=0;sms.last_error='';sms.locked_at=None
    prepare_parts(sms,enabled=live_sms_enabled(sms.invoice))
    services.audit(school,user,'sms.prepared',sms.pk)
    return sms
