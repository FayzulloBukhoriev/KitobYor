from decimal import Decimal
from django.test import TestCase
from .tests import fixture
from . import services,importing
from .models import Stock,Student

class HardeningTests(TestCase):
    def setUp(self):fixture(self);self.client.force_login(self.user)
    def test_stale_inventory_edit_does_not_recreate_issued_stock(self):
        ed=self.items[0].preferred;revision=services.inventory_revision(ed)
        Stock.objects.filter(edition=ed).update(available=1)
        with self.assertRaises(services.DomainError) as error:
            services.save_inventory(user=self.user,school=self.school,edition_id=ed.pk,title=ed.book.title,grade=5,year=ed.year,quantity=2,fee=Decimal('2.00'),expected_revision=revision)
        self.assertEqual(error.exception.code,'stale_inventory');self.assertEqual(Stock.objects.get(edition=ed).available,1)
    def test_fresh_inventory_edit(self):
        ed=self.items[0].preferred
        response=self.client.post(f'/inventory/{ed.pk}/',{'title':ed.book.title,'grade':5,'year':ed.year,'quantity':4,'fee':'3.00','expected_revision':services.inventory_revision(ed)})
        self.assertEqual(response.status_code,302);self.assertEqual(Stock.objects.get(edition=ed).available,4)
    def test_huge_query_ids_do_not_crash(self):
        self.assertEqual(self.client.get('/issue/',{'student':'9'*100}).status_code,404)
        self.assertEqual(self.client.get('/invoices/',{'q':'10'+'9'*100}).status_code,200)
        self.assertEqual(self.client.get('/students/',{'grade':'9'*6000}).status_code,200)
    def test_student_without_current_enrollment_is_handled(self):
        student=Student.objects.create(school=self.school,code='none',full_name='New',address='Test')
        self.assertEqual(self.client.get('/issue/',{'student':student.pk}).status_code,302)
    def test_invalid_csv_is_validation_error(self):
        with self.assertRaises(services.DomainError):importing.parse_upload(pasted='full_name,grade,group,address\n"unterminated')
        with self.assertRaises(services.DomainError):importing.parse_upload(pasted='full_name,grade,group,address\nName,5,A,Test,extra')
    def test_no_language_fields_in_student_and_book_forms(self):
        for url in ('/students/new/','/inventory/new/',f'/students/{self.student.pk}/edit/'):
            self.assertNotContains(self.client.get(url),'name="language"')
    def test_security_headers_private_cache_and_health(self):
        response=self.client.get('/');self.assertEqual(response['Cache-Control'],'private, no-store')
        self.assertIn("frame-ancestors 'none'",response['Content-Security-Policy'])
        self.assertEqual(self.client.get('/healthz/').json(),{'status':'ok'})
    def test_sms_and_account_are_scoped_and_password_form_exists(self):
        self.assertEqual(self.client.get('/sms/').status_code,200)
        self.assertEqual(self.client.get('/account/').status_code,200)
        self.assertContains(self.client.get('/account/password/'),'name="old_password"')
    def test_api_stale_edit_needs_revision(self):
        from rest_framework.test import APIClient
        c=APIClient();c.force_authenticate(self.user);ed=self.items[0].preferred
        response=c.post(f'/api/v1/catalog/{ed.pk}/',{'title':ed.book.title,'grade':5,'year':ed.year,'quantity':100,'fee':'2.00'},format='json')
        self.assertEqual(response.status_code,400)
    def test_inactive_user_cannot_mutate_services(self):
        self.user.is_active=False;self.user.save()
        with self.assertRaises(services.DomainError):services.add_student(user=self.user,school=self.school,full_name='No',address='Test',grade=5,group='A')
    def test_issue_validation_retains_available_selection(self):
        from uuid import uuid4
        ed=self.items[0].preferred
        r=self.client.post('/issue/',{'student_id':self.student.pk,'editions':[ed.pk],'token':str(uuid4()),'expected_total':'0.01'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(any(row.get('selected') for row in r.context['preview']['items']))
    def test_admin_login_uses_same_rate_limit(self):
        self.client.logout()
        for _ in range(5):self.client.post('/admin/login/',{'username':'unknown-admin','password':'wrong'})
        self.assertEqual(self.client.post('/admin/login/',{'username':'unknown-admin','password':'wrong'}).status_code,429)
    def test_sms_is_scoped_to_school_and_cannot_prepare_foreign_record(self):
        from .models import School,Enrollment,Loan,Invoice,SmsNotification
        from uuid import uuid4
        school=School.objects.create(code='ELSE',name='Else')
        student=Student.objects.create(school=school,code='1',full_name='Foreign student',address='Test')
        loan=Loan.objects.create(school=school,student=student,academic_year=school.academic_year,request_hash='x'*64,created_by=self.user)
        invoice=Invoice.objects.create(school=school,loan=loan)
        sms=SmsNotification.objects.create(invoice=invoice,body='Foreign',status='preview')
        self.assertNotContains(self.client.get('/sms/'),'Foreign student')
        self.client.post('/sms/',{'notification_id':sms.pk})
        sms.refresh_from_db();self.assertEqual(sms.status,'preview')
