from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from .models import School, Membership, Student, Enrollment, Book, Edition, Stock, Tariff, Kit, KitItem, Loan, Invoice, Payment
from . import services as s


def fixture(case):
    case.school=School.objects.create(name='Мактаби санҷишӣ',code='TEST')
    case.user=get_user_model().objects.create_user('admin',password='Testing-Password-123')
    Membership.objects.create(user=case.user,school=case.school,role='admin')
    case.student=Student.objects.create(school=case.school,code='001',full_name='Хонандаи санҷишӣ',address='Суроғаи санҷишӣ')
    Enrollment.objects.create(student=case.student,academic_year=case.school.academic_year,grade=5,group='А')
    case.kit=Kit.objects.create(school=case.school,name='Синфи 5',grade=5,academic_year=case.school.academic_year)
    case.items=[]
    for n in range(5):
        book=Book.objects.create(school=case.school,code=str(n),title=f'Китоб {n}',grade=5)
        ed=Edition.objects.create(book=book,code='2024',year=2024)
        Stock.objects.create(edition=ed,available=2)
        Tariff.objects.create(edition=ed,academic_year=case.school.academic_year,fee=Decimal('2.00'),approved=True,note='TEST ONLY')
        case.items.append(KitItem.objects.create(kit=case.kit,label=book.title,preferred=ed,position=n))
    case.choices=[{'kit_item_id':i.pk,'edition_id':i.preferred_id} for i in case.items]

class DomainTests(TestCase):
    def setUp(self): fixture(self)
    def issue(self,**kwargs):
        args=dict(user=self.user,school=self.school,student_id=self.student.pk,kit_id=self.kit.pk,choices=self.choices,token=uuid4(),expected_total=Decimal('10.00'))
        args.update(kwargs)
        return s.confirm_issue(**args)
    def test_issue_is_atomic_and_idempotent(self):
        token=uuid4();inv=self.issue(token=token)
        again=self.issue(token=token)
        self.assertEqual(inv.pk,again.pk);self.assertEqual(Loan.objects.count(),1)
        self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,1)
        with self.assertRaises(s.DomainError): self.issue(token=token,expected_total=Decimal('9.00'))
    def test_empty_stock_rolls_back_everything(self):
        Stock.objects.filter(edition=self.items[-1].preferred).update(available=0)
        with self.assertRaises(s.DomainError): self.issue()
        self.assertFalse(Invoice.objects.exists());self.assertFalse(Loan.objects.exists())
        self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,2)
    def test_changed_price_requires_confirmation(self):
        with self.assertRaises(s.DomainError) as ctx:self.issue(expected_total=Decimal('9.00'))
        self.assertEqual(ctx.exception.code,'price_changed');self.assertFalse(Invoice.objects.exists())
    def test_snapshot_survives_tariff_change(self):
        inv=self.issue()
        s.set_tariff(user=self.user,school=self.school,edition_id=self.items[0].preferred_id,fee=Decimal('8.00'),note='New TEST tariff',approved=True)
        inv.refresh_from_db();self.assertEqual(inv.total,Decimal('10.00'))
        self.assertEqual(inv.loan.lines.get(kit_item=self.items[0]).fee_snapshot,Decimal('2.00'))
    def test_preview_omits_unavailable_charge(self):
        Stock.objects.filter(edition=self.items[0].preferred).update(available=0)
        preview=s.preview_issue(self.school,self.student.pk,self.kit.pk)
        self.assertEqual(Decimal(preview['estimated_total']),Decimal('8.00'))
        self.assertIsNone(preview['items'][0]['suggested'])
    def test_partial_requires_explicit_acceptance(self):
        with self.assertRaises(s.DomainError) as ctx:self.issue(choices=self.choices[:1],expected_total=Decimal('2.00'))
        self.assertEqual(ctx.exception.code,'partial_required')
        self.assertEqual(self.issue(choices=self.choices[:1],expected_total=Decimal('2.00'),allow_partial=True).total,Decimal('2.00'))
    def test_return_does_not_clear_debt_and_is_repeat_safe(self):
        inv=self.issue();line=inv.loan.lines.first();args=dict(user=self.user,school=self.school,loan_id=inv.loan_id,lines=[{'line_id':line.pk,'state':'returned'}])
        s.close_lines(**args);s.close_lines(**args)
        inv.refresh_from_db();self.assertEqual(inv.balance,Decimal('10.00'))
        self.assertEqual(Stock.objects.get(edition=line.edition).available,2)
    def test_payment_idempotency_and_no_overpayment(self):
        inv=self.issue();args=dict(user=self.user,school=self.school,invoice_id=inv.pk,amount=Decimal('4.00'),receipt='TEST-1',note='TEST ONLY',token=uuid4())
        p=s.record_payment(**args);self.assertEqual(p.pk,s.record_payment(**args).pk)
        inv.refresh_from_db();self.assertEqual(inv.balance,Decimal('6.00'));self.assertEqual(Payment.objects.count(),1)
        args.update(amount=Decimal('7.00'),receipt='TEST-2',token=uuid4())
        with self.assertRaises(s.DomainError):s.record_payment(**args)
        self.assertEqual(Payment.objects.count(),1)
    def test_duplicate_active_issue_rejected(self):
        self.issue()
        with self.assertRaises(s.DomainError) as ctx:self.issue()
        self.assertEqual(ctx.exception.code,'already_held')
    def test_kit_must_match_current_enrollment(self):
        Enrollment.objects.filter(student=self.student).update(grade=6)
        with self.assertRaises(s.DomainError):self.issue()
    def test_other_school_student_is_inaccessible(self):
        other=School.objects.create(name='Дигар',code='OTHER')
        student=Student.objects.create(school=other,code='1',full_name='Дигар',address='Test')
        with self.assertRaises(s.DomainError) as ctx:self.issue(student_id=student.pk)
        self.assertEqual(ctx.exception.status,404)
    def test_api_scope_and_role(self):
        other=School.objects.create(name='Дигар',code='OTHER')
        Student.objects.create(school=other,code='1',full_name='Дигар',address='Test')
        client=APIClient();client.force_authenticate(self.user)
        res=client.get('/api/v1/students/');self.assertEqual(res.status_code,200);self.assertEqual(res.data['count'],1)
        Membership.objects.filter(user=self.user).update(role='viewer')
        self.assertEqual(client.post('/api/v1/students/',{},format='json').status_code,403)
    def test_session_api_requires_csrf(self):
        client=APIClient(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post('/api/v1/students/',{},format='json').status_code,403)
    def test_login_throttling_and_templates(self):
        self.assertContains(self.client.get('/login/'),'KitobYor')
        for _ in range(5):self.client.post('/login/',{'username':'unknown','password':'wrong'})
        self.assertEqual(self.client.post('/login/',{'username':'unknown','password':'wrong'}).status_code,429)
        self.client.force_login(self.user);self.assertContains(self.client.get('/'),'Раванди содаи иҷора')
    def test_cross_school_api_mutation(self):
        other=School.objects.create(name='Дигар',code='OTHER')
        book=Book.objects.create(school=other,code='1',title='Other',grade=5)
        ed=Edition.objects.create(book=book,code='1',year=2024);Stock.objects.create(edition=ed)
        client=APIClient();client.force_authenticate(self.user)
        self.assertEqual(client.post(f'/api/v1/editions/{ed.pk}/intake/',{'quantity':1,'note':'Test'},format='json').status_code,404)
        self.assertEqual(Stock.objects.get(edition=ed).available,0)

@skipUnless(connection.vendor=='postgresql','Requires PostgreSQL row locks; run CI or native PostgreSQL tests')
class PostgreSQLConcurrencyTests(TransactionTestCase):
    def setUp(self):fixture(self)
    def test_last_copy_cannot_be_issued_twice(self):
        Stock.objects.filter(edition=self.items[0].preferred).update(available=1)
        other=Student.objects.create(school=self.school,code='002',full_name='Дуюм',address='Test')
        Enrollment.objects.create(student=other,academic_year=self.school.academic_year,grade=5,group='А')
        def issue(student_id):
            close_old_connections()
            try:
                s.confirm_issue(user=get_user_model().objects.get(pk=self.user.pk),school=School.objects.get(pk=self.school.pk),student_id=student_id,kit_id=self.kit.pk,choices=self.choices[:1],token=uuid4(),expected_total=Decimal('2.00'),allow_partial=True)
                return 'ok'
            except s.DomainError as exc:return exc.code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(issue,[self.student.pk,other.pk]))
        self.assertCountEqual(results,['ok','stock_changed'])
        self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,0)
        self.assertEqual(Invoice.objects.count(),1)
    def test_catalog_last_copy_cannot_be_issued_twice(self):
        Stock.objects.filter(edition=self.items[0].preferred).update(available=1)
        other=Student.objects.create(school=self.school,code='C002',full_name='Дуюм',address='Test')
        Enrollment.objects.create(student=other,academic_year=self.school.academic_year,grade=5,group='B')
        def issue(student_id):
            close_old_connections()
            try:
                s.confirm_catalog_issue(user=get_user_model().objects.get(pk=self.user.pk),school=School.objects.get(pk=self.school.pk),student_id=student_id,edition_ids=[self.items[0].preferred_id],token=uuid4(),expected_total=Decimal('2.00'))
                return 'ok'
            except s.DomainError as exc:return exc.code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(issue,[self.student.pk,other.pk]))
        self.assertCountEqual(results,['ok','stock_changed'])
        self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,0)
        self.assertEqual(Invoice.objects.count(),1)
