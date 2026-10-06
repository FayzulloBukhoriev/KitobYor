"""Operator-assisted reconciliation after ambiguous modem submission."""
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from django.utils import timezone
from library.models import SmsNotification,Membership
from library import services

class Command(BaseCommand):
    help='Resolve one uncertain SMS part only after checking the modem/operator records.'
    def add_arguments(self,p):
        p.add_argument('--id',type=int,required=True);p.add_argument('--part',type=int,required=True)
        p.add_argument('--operator',required=True,help='School admin username for audit.')
        p.add_argument('--outcome',choices=['accepted','not-sent'],required=True)
        p.add_argument('--reference',required=True,help='Reference to the checked modem/operator record.')
        p.add_argument('--verified',action='store_true',help='Confirm records were checked; incorrect not-sent may duplicate SMS.')
    @transaction.atomic
    def handle(self,*args,**opts):
        if not opts['verified']:raise CommandError('Verify modem/operator records first; then pass --verified. A wrong decision can duplicate SMS.')
        sms=SmsNotification.objects.select_for_update().filter(pk=opts['id']).first()
        if not sms or sms.status not in ['uncertain','failed']:raise CommandError('SMS must be uncertain or failed.')
        member=Membership.objects.select_related('user').filter(school=sms.invoice.school,user__username=opts['operator'],role='admin',user__is_active=True).first()
        if not member:raise CommandError('Active administrator of this school required.')
        part=sms.parts.filter(sequence=opts['part'],status__in=['uncertain','submitting','pending']).first()
        if not part:raise CommandError('Unresolved part not found; accepted parts cannot be reset.')
        reference=opts['reference'].strip()
        if not reference or len(reference)>120:raise CommandError('A reference of 1–120 characters is required.')
        part.status='submitted' if opts['outcome']=='accepted' else 'pending'
        part.reference='manual:'+reference[:25] if opts['outcome']=='accepted' else ''
        part.submitted_at=timezone.now() if opts['outcome']=='accepted' else None;part.save()
        if sms.parts.filter(status__in=['uncertain','submitting']).exists():sms.status='uncertain'
        elif sms.parts.filter(status='pending').exists():sms.status='queued'
        else:sms.status='submitted';sms.sent_at=timezone.now()
        sms.attempts=0;sms.locked_at=None;sms.last_error='';sms.next_attempt_at=timezone.now();sms.save()
        services.audit(sms.invoice.school,member.user,'sms.reconciled',sms.pk,f'part={part.sequence}; {opts["outcome"]}; ref={reference}')
        self.stdout.write(self.style.SUCCESS(f'SMS #{sms.pk}: {sms.status}'))
