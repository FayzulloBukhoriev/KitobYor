"""Idempotent demo school seeding. Does not modify another school or reset credentials."""
import os
import secrets
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from library.models import School,Membership,Student,Enrollment,Book,Edition,Stock,Kit,Invoice,Payment
from library import services

class Command(BaseCommand):
    help='Create a fictional DEMO school. Prints generated login once; existing login is preserved.'
    def add_arguments(self,parser):
        parser.add_argument('--reset-password',action='store_true',help='Reset only the DEMO account password (explicit).')
    @transaction.atomic
    def handle(self,*args,**opts):
        User=get_user_model();username='demo'
        school,_=School.objects.get_or_create(code='DEMO',defaults={'name':'Мактаби намунавии KitobYor','academic_year':'2026-2027'})
        user=User.objects.filter(username=username).first()
        new=not bool(user)
        if user and not Membership.objects.filter(user=user,school=school).exists():raise CommandError('Username demo belongs to another school. Nothing changed.')
        if new:user=User.objects.create(username=username)
        if new or opts['reset_password']:
            password=os.environ.get('KITOBYOR_DEMO_PASSWORD') or secrets.token_urlsafe(12)
            if len(password)<10:raise CommandError('Demo password must have at least 10 characters.')
            user.set_password(password);user.save()
            self.stdout.write(f'\nDEMO LOGIN: {username}\nDEMO PASSWORD: {password}\nKeep this password. This is fictional local demo data.\n')
        Membership.objects.get_or_create(user=user,defaults={'school':school,'role':'admin'})
        titles=['Забони тоҷикӣ','Математика','Табиатшиносӣ','Таърихи халқи тоҷик','Забони русӣ','Забони англисӣ']
        names=['Хонандаи намунавӣ 01','Хонандаи намунавӣ 02','Хонандаи намунавӣ 03','Хонандаи намунавӣ 04','Хонандаи намунавӣ 05','Хонандаи намунавӣ 06','Хонандаи намунавӣ 07','Хонандаи намунавӣ 08','Хонандаи намунавӣ 09','Хонандаи намунавӣ 10']
        for grade in (5,6,7):
            items=[]
            for n,title in enumerate(titles,1):
                book,_=Book.objects.get_or_create(school=school,code=f'D{grade}-{n}',defaults={'title':title,'grade':grade,'language':'Тоҷикӣ'})
                editions=[]
                for year,fee in ((2025,Decimal('3.50')),(2020,Decimal('2.00'))):
                    ed,created=Edition.objects.get_or_create(book=book,code=f'{year}-DEMO',defaults={'year':year,'publisher':'Нашриёти намунавӣ'})
                    Stock.objects.get_or_create(edition=ed)
                    if created:
                        services.intake(user=user,school=school,edition_id=ed.pk,quantity=18 if year==2025 else 8,note='DEMO: воридшавии намунавӣ')
                        services.set_tariff(user=user,school=school,edition_id=ed.pk,fee=fee,note='DEMO: нархи сохта барои намоиш, тарифи расмӣ нест',approved=True)
                    editions.append(ed)
                items.append({'preferred_id':editions[0].pk,'alternative_ids':[editions[1].pk]})
            kit=Kit.objects.filter(school=school,grade=grade,language='Тоҷикӣ',academic_year=school.academic_year).first()
            if not kit:kit=services.create_kit(user=user,school=school,name=f'Маҷмӯаи синфи {grade}',grade=grade,language='Тоҷикӣ',items=items)
            for index,name in enumerate(names,1):
                code=f'D{grade}-{index:03}'
                student=Student.objects.filter(school=school,code=code).first()
                if not student:student=services.add_student(user=user,school=school,code=code,full_name=f'{name} · синфи {grade}',address='Суроғаи сохта барои намоиш',grade=grade,group='A' if index<=5 else 'B',language='Тоҷикӣ',parent_name='Намояндаи намунавӣ',parent_phone='+992000000000')
                if index<=3 and not student.loans.exists():
                    preview=services.preview_issue(school,student.pk,kit.pk)
                    choices=[{'kit_item_id':r['kit_item_id'],'edition_id':r['suggested']['edition_id']} for r in preview['items'] if r['suggested']]
                    inv=services.confirm_issue(user=user,school=school,student_id=student.pk,kit_id=kit.pk,choices=choices,token=uuid4(),expected_total=Decimal(preview['estimated_total']),allow_partial=len(choices)<len(items))
                    if index==1:services.record_payment(user=user,school=school,invoice_id=inv.pk,amount=inv.total,receipt=f'DEMO-{grade}-1',note='DEMO: пардохти намунавӣ',token=uuid4())
                    if index==2:services.record_payment(user=user,school=school,invoice_id=inv.pk,amount=Decimal('10.00'),receipt=f'DEMO-{grade}-2',note='DEMO: пардохти қисман',token=uuid4())
        from library.notifications import prepare_sms
        for invoice in Invoice.objects.filter(school=school):prepare_sms(invoice)
        self.stdout.write(self.style.SUCCESS('DEMO ready: 30 students, 36 editions, 3 kits. Existing data preserved.'))
