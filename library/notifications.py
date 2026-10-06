"""Notification preparation only. No SMS is sent until an authorized provider is integrated."""
from .models import SmsNotification

def prepare_sms(invoice):
    student=invoice.loan.student
    phone=student.parent_phone
    body=(f'{invoice.school.name}: {student.full_name} — иҷораи китобҳо {invoice.total:.2f} сомонӣ. '
          f'Рақами дохилии пардохт: {invoice.payment_number}. '
          'Барои пардохт ба мактаб муроҷиат кунед. Пайвасти бонк ҳоло фаъол нест.')
    notification,_=SmsNotification.objects.get_or_create(invoice=invoice,defaults={'destination':phone,'body':body,'status':'preview' if phone else 'missing_phone'})
    return notification
