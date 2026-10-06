import io
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .tests import fixture
from .models import Student,Invoice,ImportBatch,Membership,Stock,Kit,Enrollment
from . import services, importing

class WorkspaceTests(TestCase):
    def setUp(self):fixture(self);self.client.force_login(self.user)
    def test_all_workspace_pages_render(self):
        for name in ['dashboard','students','inventory','kits','issue','invoices','returns','reports','student_new','catalog_new','kit_new','student_import']:
            with self.subTest(name=name):self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertEqual(self.client.get(reverse('edition_detail',args=[self.items[0].preferred_id])).status_code,200)
    def test_student_add_edit(self):
        data={'code':'NEW','full_name':'Хонандаи нав','address':'Суроға','grade':5,'group':'Б','language':'Тоҷикӣ'}
        self.assertRedirects(self.client.post(reverse('student_new'),data),reverse('students'))
        student=Student.objects.get(code='NEW');data['full_name']='Номи таҳриршуда'
        self.assertRedirects(self.client.post(reverse('student_edit',args=[student.pk]),data),reverse('students'))
        student.refresh_from_db();self.assertEqual(student.full_name,'Номи таҳриршуда')
        self.assertEqual(Enrollment.objects.filter(student=student).count(),1)
    def test_student_filters_use_current_enrollment_only(self):
        Enrollment.objects.create(student=self.student,academic_year='2025-2026',grade=4,group='Б')
        response=self.client.get(reverse('students'),{'grade':'5','group':'Б'})
        self.assertEqual(response.context['rows'].paginator.count,0)
    def test_import_preview_confirm_atomic(self):
        content='code,full_name,grade,group,address,language\nNEW01,Хонандаи аввал,5,А,Суроға,Тоҷикӣ\nNEW02,Хонандаи дуюм,5,Б,Суроға,Тоҷикӣ\n'
        response=self.client.post(reverse('student_import'),{'pasted':content})
        self.assertEqual(response.status_code,200);self.assertFalse(Student.objects.filter(code='NEW01').exists())
        token=self.client.session['student_import']['token']
        self.assertRedirects(self.client.post(reverse('student_import'),{'action':'commit','token':token}),reverse('students'))
        self.assertEqual(Student.objects.filter(code__startswith='NEW').count(),2);self.assertEqual(ImportBatch.objects.count(),1)
    def test_import_invalid_batch_never_partially_commits(self):
        rows=[dict(code='NEW',full_name='New',grade='5',group='А',address='Test',language='Тоҷикӣ'),dict(code='BAD',full_name='Bad',grade='12',group='А',address='Test',language='Тоҷикӣ')]
        with self.assertRaises(services.DomainError):importing.commit_import(user=self.user,school=self.school,rows=rows,token=uuid4(),file_hash='a'*64)
        self.assertFalse(Student.objects.filter(code='NEW').exists())
    def test_import_revalidation_catches_new_duplicate(self):
        rows=[dict(code='NEW',full_name='New',grade='5',group='А',address='Test',language='Тоҷикӣ')]
        services.add_student(user=self.user,school=self.school,**{**rows[0],'grade':5})
        with self.assertRaises(services.DomainError):importing.commit_import(user=self.user,school=self.school,rows=rows,token=uuid4(),file_hash='a'*64)
        self.assertFalse(ImportBatch.objects.exists())
    def test_import_xlsx_and_paste(self):
        from openpyxl import Workbook
        wb=Workbook();ws=wb.active;ws.append(importing.HEADERS);ws.append(['X01','Хонанда',5,'А','Test','Тоҷикӣ']);stream=io.BytesIO();wb.save(stream)
        file=SimpleUploadedFile('students.xlsx',stream.getvalue())
        rows,digest=importing.parse_upload(file);self.assertEqual(rows[0]['grade'],'5')
        checked,valid=importing.validate_rows(rows,self.school);self.assertEqual(len(valid),1)
    def test_issue_payment_return_html_flow(self):
        response=self.client.get(reverse('issue'),{'student':self.student.pk});self.assertContains(response,'Тасдиқи додани китоб')
        data={'student_id':self.student.pk,'token':str(uuid4()),'expected_total':'10.00'}
        data.update({f'choice_{c["kit_item_id"]}':c['edition_id'] for c in self.choices})
        response=self.client.post(reverse('issue'),data);self.assertEqual(response.status_code,302)
        inv=Invoice.objects.get();self.assertEqual(response.url,reverse('invoice_detail',args=[inv.pk]))
        response=self.client.post(response.url,{'action':'payment','amount':'4.00','receipt':'UI-1','note':'Test','token':str(uuid4())});self.assertEqual(response.status_code,302)
        inv.refresh_from_db();self.assertEqual(inv.balance,Decimal('6.00'))
        line=inv.loan.lines.first()
        response=self.client.post(reverse('invoice_detail',args=[inv.pk]),{'action':'return',f'return_{line.pk}':'on',f'state_{line.pk}':'returned'})
        self.assertEqual(response.status_code,302);line.refresh_from_db();self.assertEqual(line.state,'returned')
        inv.refresh_from_db();self.assertEqual(inv.balance,Decimal('6.00'))
    def test_ui_role_and_tenant_protection(self):
        Membership.objects.filter(user=self.user).update(role='viewer')
        for name in ['student_new','student_import','catalog_new','kit_new','issue']:
            self.assertEqual(self.client.get(reverse(name)).status_code,403)
        response=self.client.post(reverse('edition_detail',args=[self.items[0].preferred_id]),{'action':'intake','intake-quantity':100,'intake-note':'Test'})
        self.assertEqual(response.status_code,200);self.assertEqual(Stock.objects.get(edition=self.items[0].preferred).available,2)
    def test_csv_formula_neutralization(self):
        self.items[0].preferred.book.title='=HYPERLINK("bad")';self.items[0].preferred.book.save()
        response=self.client.get(reverse('export'),{'kind':'stock'})
        self.assertIn("'=HYPERLINK",response.content.decode('utf-8'))
    def test_import_retry_is_idempotent(self):
        rows=[dict(code='NEW',full_name='New',grade='5',group='А',address='Test',language='Тоҷикӣ')];token=uuid4()
        args=dict(user=self.user,school=self.school,rows=rows,token=token,file_hash='a'*64)
        self.assertEqual(importing.commit_import(**args),1);self.assertEqual(importing.commit_import(**args),0)
    def test_seed_demo_is_idempotent(self):
        import os
        from unittest.mock import patch
        out=io.StringIO()
        with patch.dict(os.environ,{'KITOBYOR_DEMO_PASSWORD':'Test-only-generated-123'}):call_command('seed_demo',stdout=out)
        students=Student.objects.count();invoices=Invoice.objects.count();kits=Kit.objects.count()
        call_command('seed_demo',stdout=out)
        self.assertEqual(Student.objects.count(),students);self.assertEqual(Invoice.objects.count(),invoices);self.assertEqual(Kit.objects.count(),kits)
