from decimal import Decimal
from uuid import uuid4
from django.test import TestCase,TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient
from .tests import fixture
from .models import Book,Edition,Stock,Loan,Invoice,Payment,SmsNotification,Student,Enrollment,KitItem,Kit,Membership
from . import services

class VersionOneTests(TestCase):
    def setUp(self):fixture(self);self.client.force_login(self.user)
    def issue(self,ids=None,**overrides):
        data=dict(user=self.user,school=self.school,student_id=self.student.pk,edition_ids=ids or [self.items[0].preferred_id],expected_total=Decimal('2.00'),token=uuid4())
        data.update(overrides);return services.confirm_catalog_issue(**data)
    def test_no_kit_required(self):
        KitItem.objects.all().delete();Kit.objects.all().delete()
        invoice=self.issue();self.assertIsNone(invoice.loan.kit_id);self.assertIsNone(invoice.loan.lines.first().kit_item_id)
        self.assertTrue(invoice.payment_number.isdigit());self.assertEqual(len(invoice.payment_number),14)
    def test_inventory_auto_groups_years_and_separate_prices(self):
        ed=services.save_inventory(user=self.user,school=self.school,title='Китоб 0',grade=5,year=2020,quantity=5,fee=Decimal('1.00'))
        self.assertEqual(ed.book_id,self.items[0].preferred.book_id)
        row=next(r for r in services.preview_catalog(self.school,self.student.pk)['items'] if r['book_id']==ed.book_id)
        self.assertEqual(len(row['choices']),2)
        invoice=self.issue([ed.pk],expected_total=Decimal('1.00'))
        self.assertEqual(invoice.total,Decimal('1.00'));self.assertEqual(Stock.objects.get(edition=ed).available,4)
    def test_two_years_of_same_book_rejected(self):
        ed=services.save_inventory(user=self.user,school=self.school,title='Китоб 0',grade=5,year=2020,quantity=5,fee=Decimal('1.00'))
        with self.assertRaises(services.DomainError):self.issue([ed.pk,self.items[0].preferred_id],expected_total=Decimal('3.00'))
        self.assertFalse(Loan.objects.exists())
    def test_wrong_grade_and_foreign_school_rejected(self):
        self.items[0].preferred.book.grade=6;self.items[0].preferred.book.save()
        with self.assertRaises(services.DomainError):self.issue()
        from .models import School
        other=School.objects.create(name='Other',code='OTHER')
        book=Book.objects.create(school=other,code='1',title='Other',grade=5)
        ed=Edition.objects.create(book=book,code='1',year=2025)
        with self.assertRaises(services.DomainError) as ctx:self.issue([ed.pk])
        self.assertEqual(ctx.exception.status,404)
    def test_stock_rollback_and_price_changed(self):
        Stock.objects.filter(edition=self.items[1].preferred).update(available=0)
        with self.assertRaises(services.DomainError):self.issue([i.preferred_id for i in self.items[:2]],expected_total=Decimal('4.00'))
        self.assertFalse(Invoice.objects.exists());self.assertFalse(SmsNotification.objects.exists())
        self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,2)
        with self.assertRaises(services.DomainError) as ctx:self.issue(expected_total=Decimal('1.00'))
        self.assertEqual(ctx.exception.code,'price_changed')
    def test_issue_idempotency_and_duplicate_book_across_editions(self):
        token=uuid4();inv=self.issue(token=token);self.assertEqual(inv.pk,self.issue(token=token).pk)
        self.assertEqual(SmsNotification.objects.count(),1)
        ed=services.save_inventory(user=self.user,school=self.school,title='Китоб 0',grade=5,year=2020,quantity=5,fee=Decimal('1.00'))
        with self.assertRaises(services.DomainError) as ctx:self.issue([ed.pk],expected_total=Decimal('1.00'))
        self.assertEqual(ctx.exception.code,'already_held')
    def test_sms_is_preview_never_sent(self):
        self.student.parent_phone='+992000000000';self.student.save()
        inv=self.issue();sms=inv.sms_notification
        self.assertEqual(sms.status,'preview');self.assertIsNone(sms.sent_at)
        self.assertIn(inv.payment_number,sms.body);self.assertIn('2.00',sms.body);self.assertIn('ҳоло фаъол нест',sms.body)
    def test_cash_paid_one_click_and_idempotent(self):
        inv=self.issue();url=f'/invoices/{inv.pk}/'
        self.assertEqual(self.client.post(url,{'action':'paid'}).status_code,302)
        self.assertEqual(self.client.post(url,{'action':'paid'}).status_code,302)
        inv.refresh_from_db();self.assertEqual(inv.paid,inv.total);self.assertEqual(Payment.objects.count(),1)
    def test_cash_works_for_partial_legacy_invoice(self):
        inv=self.issue();services.record_payment(user=self.user,school=self.school,invoice_id=inv.pk,amount=Decimal('0.50'),receipt='TEST',note='Test',token=uuid4())
        services.mark_cash_paid(user=self.user,school=self.school,invoice_id=inv.pk)
        inv.refresh_from_db();self.assertEqual(inv.paid,Decimal('2.00'));self.assertEqual(Payment.objects.last().amount,Decimal('1.50'))
    def test_cash_permission_and_foreign_invoice(self):
        inv=self.issue();Membership.objects.filter(user=self.user).update(role='librarian')
        with self.assertRaises(services.DomainError) as ctx:services.mark_cash_paid(user=self.user,school=self.school,invoice_id=inv.pk)
        self.assertEqual(ctx.exception.status,403)
        inv.refresh_from_db();self.assertEqual(inv.paid,0)
    def test_inventory_edit_preserves_invoice_snapshot(self):
        inv=self.issue();ed=self.items[0].preferred
        services.save_inventory(user=self.user,school=self.school,edition_id=ed.pk,title='Китоб 0 нав',grade=5,year=2025,quantity=7,fee=Decimal('8.00'))
        inv.refresh_from_db();line=inv.loan.lines.first()
        self.assertEqual(inv.total,Decimal('2.00'));self.assertEqual(line.title_snapshot,'Китоб 0');self.assertEqual(line.year_snapshot,2024)
        self.assertEqual(Stock.objects.get(edition=ed).available,7)
    def test_ui_forms_hide_codes_and_groups_select(self):
        r=self.client.get('/students/new/');self.assertNotContains(r,'name="code"');self.assertContains(r,'name="parent_phone"')
        r=self.client.get('/inventory/new/')
        for field in ['book_code','edition_code','isbn','publisher','language']:self.assertNotContains(r,f'name="{field}"')
        for field in ['quantity','fee']:self.assertContains(r,f'name="{field}"')
        r=self.client.get('/students/');self.assertContains(r,'<select aria-label="Гурӯҳ"');self.assertNotContains(r,'Рамз')
    def test_phone_normalization_and_invalid_phone_atomic(self):
        from django.core.exceptions import ValidationError
        data=dict(user=self.user,school=self.school,full_name='Phone test',address='Test',grade=5,group='B')
        student=services.add_student(**data,parent_phone='900 000 000')
        self.assertEqual(student.parent_phone,'+992900000000')
        with self.assertRaises(ValidationError):services.add_student(**data,parent_phone='bad')
        self.assertEqual(Student.objects.filter(full_name='Phone test').count(),1)
    def test_import_auto_codes_blocks_repeat_profile_with_new_token(self):
        from . import importing
        rows=[dict(full_name='Import test',grade='5',group='B',address='Test',parent_phone='900000000')]
        args=dict(user=self.user,school=self.school,rows=rows,file_hash='b'*64)
        self.assertEqual(importing.commit_import(**args,token=uuid4()),1)
        with self.assertRaises(services.DomainError):importing.commit_import(**args,token=uuid4())
        self.assertEqual(Student.objects.filter(full_name='Import test').count(),1)
    def test_report_has_one_row_per_invoice_and_status_filters(self):
        inv=self.issue([i.preferred_id for i in self.items],expected_total=Decimal('10.00'))
        import csv,io
        rows=list(csv.reader(io.StringIO(self.client.get('/reports/export/').content.decode('utf-8-sig'))))
        self.assertEqual(len(rows),2);self.assertEqual(rows[1][4],'5');self.assertEqual(rows[1][6],'10.00')
        self.assertEqual(self.client.get('/invoices/?status=unpaid').context['rows'].paginator.count,1)
        services.mark_cash_paid(user=self.user,school=self.school,invoice_id=inv.pk)
        self.assertEqual(self.client.get('/invoices/?status=paid').context['rows'].paginator.count,1)
        self.assertEqual(self.client.get('/invoices/?status=unpaid').context['rows'].paginator.count,0)
    def test_simplified_api_requires_correct_roles(self):
        client=APIClient();client.force_authenticate(self.user)
        r=client.post('/api/v1/catalog/issues/confirm/',{'student_id':self.student.pk,'edition_ids':[self.items[0].preferred_id],'expected_total':'2.00','token':str(uuid4())},format='json')
        self.assertEqual(r.status_code,200);self.assertTrue(r.data['payment_number'].isdigit())
        self.assertEqual(client.post(f'/api/v1/invoices/{r.data["id"]}/paid/',{},format='json').status_code,200)
        self.assertEqual(client.get('/api/v1/loans/1/returns/').status_code,404)

class UpgradeMigrationTests(TransactionTestCase):
    def test_02_history_survives_upgrade(self):
        executor=MigrationExecutor(connection);executor.migrate([('library','0001_initial')])
        apps=executor.loader.project_state([('library','0001_initial')]).apps
        User=apps.get_model('auth','User');user=User.objects.create(username='migration')
        School=apps.get_model('library','School');school=School.objects.create(name='Old school',code='OLD')
        student=apps.get_model('library','Student').objects.create(school=school,code='OLD1',full_name='Old student',address='Test')
        apps.get_model('library','Enrollment').objects.create(student=student,academic_year=school.academic_year,grade=5,group='Б')
        book=apps.get_model('library','Book').objects.create(school=school,code='B1',title='Old book',grade=5)
        ed=apps.get_model('library','Edition').objects.create(book=book,code='E1',year=2020)
        apps.get_model('library','Stock').objects.create(edition=ed,available=4)
        tariff=apps.get_model('library','Tariff').objects.create(edition=ed,academic_year=school.academic_year,fee=Decimal('2.00'),approved=True)
        kit=apps.get_model('library','Kit').objects.create(school=school,name='Old kit',grade=5,academic_year=school.academic_year)
        item=apps.get_model('library','KitItem').objects.create(kit=kit,label='Old book',preferred=ed)
        loan=apps.get_model('library','Loan').objects.create(school=school,student=student,kit=kit,academic_year=school.academic_year,request_hash='a'*64,created_by=user)
        apps.get_model('library','LoanLine').objects.create(loan=loan,student=student,edition=ed,kit_item=item,tariff=tariff,title_snapshot='Old book',year_snapshot=2020,fee_snapshot=Decimal('2.00'))
        invoice=apps.get_model('library','Invoice').objects.create(school=school,loan=loan,total=Decimal('2.00'),paid=Decimal('1.00'))
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
        self.assertEqual(Invoice.objects.get(pk=invoice.pk).paid,Decimal('1.00'))
        self.assertEqual(Enrollment.objects.get(student_id=student.pk).group,'B')
        self.assertEqual(Student.objects.get(pk=student.pk).parent_phone,'')
        self.assertEqual(Stock.objects.get(edition_id=ed.pk).available,4)
        self.assertEqual(Invoice.objects.get(pk=invoice.pk).loan.lines.first().fee_snapshot,Decimal('2.00'))
    def tearDown(self):
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes());super().tearDown()
