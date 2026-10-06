"""Tenant-scoped domain schema. Financial writes go through library.services."""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

GRADE = [MinValueValidator(1), MaxValueValidator(11)]
MONEY = [MinValueValidator(Decimal('0.00'))]

class School(models.Model):
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=24, unique=True)
    academic_year = models.CharField(max_length=9, default='2026-2027')
    def __str__(self): return self.name

class Membership(models.Model):
    ROLES = [('admin','Маъмур'),('librarian','Китобдор'),('accountant','Муҳосиб'),('viewer','Роҳбар')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membership')
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=ROLES, default='librarian')
    def __str__(self): return f'{self.user} / {self.school}'

class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    code = models.CharField(max_length=40)
    full_name = models.CharField(max_length=200)
    address = models.CharField(max_length=250)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ['full_name','id']
        constraints = [models.UniqueConstraint(fields=['school','code'], name='student_school_code')]
    def __str__(self): return self.full_name

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='enrollments')
    academic_year = models.CharField(max_length=9)
    grade = models.PositiveSmallIntegerField(validators=GRADE)
    group = models.CharField(max_length=8, default='А')
    language = models.CharField(max_length=40, default='Тоҷикӣ')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','academic_year'],name='student_year_enrollment'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='enrollment_grade_range')]
        indexes = [models.Index(fields=['academic_year','grade','group'])]

class Book(models.Model):
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    code = models.CharField(max_length=60)
    title = models.CharField(max_length=180)
    subject = models.CharField(max_length=80, blank=True)
    grade = models.PositiveSmallIntegerField(validators=GRADE)
    language = models.CharField(max_length=40, default='Тоҷикӣ')
    class Meta:
        ordering = ['grade','title','id']
        constraints = [models.UniqueConstraint(fields=['school','code'],name='book_school_code'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='book_grade_range')]
    def __str__(self): return self.title

class Edition(models.Model):
    book = models.ForeignKey(Book,on_delete=models.PROTECT,related_name='editions')
    code = models.CharField(max_length=60)
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1900),MaxValueValidator(2100)])
    publisher = models.CharField(max_length=120, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    class Meta:
        ordering = ['-year','id']
        constraints = [models.UniqueConstraint(fields=['book','code'],name='book_edition_code'),models.CheckConstraint(condition=Q(year__gte=1900,year__lte=2100),name='edition_year_range')]
    def __str__(self): return f'{self.book} / {self.year} / {self.code}'

class Stock(models.Model):
    edition = models.OneToOneField(Edition,on_delete=models.PROTECT,related_name='stock')
    available = models.PositiveIntegerField(default=0)
    damaged = models.PositiveIntegerField(default=0)

class Tariff(models.Model):
    edition = models.ForeignKey(Edition,on_delete=models.PROTECT,related_name='tariffs')
    academic_year = models.CharField(max_length=9)
    fee = models.DecimalField(max_digits=10,decimal_places=2,validators=MONEY)
    approved = models.BooleanField(default=False)
    note = models.CharField(max_length=250, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['edition','academic_year'],name='edition_year_tariff'),models.CheckConstraint(condition=Q(fee__gte=0),name='tariff_fee_positive')]

class Kit(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    grade = models.PositiveSmallIntegerField(validators=GRADE)
    language = models.CharField(max_length=40,default='Тоҷикӣ')
    academic_year = models.CharField(max_length=9)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['school','grade','language','academic_year'],name='one_class_kit'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='kit_grade_range')]
    def __str__(self): return self.name

class KitItem(models.Model):
    kit = models.ForeignKey(Kit,on_delete=models.PROTECT,related_name='items')
    label = models.CharField(max_length=180)
    preferred = models.ForeignKey(Edition,on_delete=models.PROTECT,related_name='+')
    alternatives = models.ManyToManyField(Edition,blank=True,related_name='+')
    position = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['position','id']
        constraints = [models.UniqueConstraint(fields=['kit','label'],name='kit_unique_label')]

class Loan(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='loans')
    kit = models.ForeignKey(Kit,on_delete=models.PROTECT)
    academic_year = models.CharField(max_length=9)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    request_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-id']

class LoanLine(models.Model):
    loan = models.ForeignKey(Loan,on_delete=models.PROTECT,related_name='lines')
    student = models.ForeignKey(Student,on_delete=models.PROTECT)
    edition = models.ForeignKey(Edition,on_delete=models.PROTECT)
    kit_item = models.ForeignKey(KitItem,on_delete=models.PROTECT)
    tariff = models.ForeignKey(Tariff,on_delete=models.PROTECT)
    title_snapshot = models.CharField(max_length=180)
    year_snapshot = models.PositiveSmallIntegerField()
    fee_snapshot = models.DecimalField(max_digits=10,decimal_places=2)
    state = models.CharField(max_length=12,choices=[('issued','Дода'),('returned','Солим'),('damaged','Осебдида'),('lost','Гумшуда')],default='issued')
    closed_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','kit_item'],condition=Q(state='issued'),name='one_active_kit_item'),models.UniqueConstraint(fields=['student','edition'],condition=Q(state='issued'),name='one_active_student_edition'),models.CheckConstraint(condition=Q(fee_snapshot__gte=0),name='line_fee_positive'),models.CheckConstraint(condition=(Q(state='issued',closed_at__isnull=True)|Q(state__in=['returned','damaged','lost'],closed_at__isnull=False)),name='loan_line_state_time')]

class Invoice(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    loan = models.OneToOneField(Loan,on_delete=models.PROTECT,related_name='invoice')
    reference = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    total = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    paid = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-id']
        constraints = [models.CheckConstraint(condition=Q(total__gte=0,paid__gte=0,paid__lte=models.F('total')),name='invoice_money_range')]
    @property
    def balance(self): return self.total-self.paid
    @property
    def number(self): return f'KY-{self.pk:08d}'

class Payment(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    invoice = models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name='payments')
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    receipt = models.CharField(max_length=120)
    note = models.CharField(max_length=250)
    token = models.UUIDField(default=uuid.uuid4,unique=True)
    request_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['school','receipt'],name='unique_payment_receipt'),models.CheckConstraint(condition=Q(amount__gt=0),name='payment_amount_positive')]

class StockMovement(models.Model):
    edition = models.ForeignKey(Edition,on_delete=models.PROTECT,related_name='movements')
    delta_available = models.IntegerField()
    delta_damaged = models.IntegerField(default=0)
    kind = models.CharField(max_length=20)
    object_id = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=250)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class AuditEvent(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    action = models.CharField(max_length=60)
    object_id = models.CharField(max_length=80)
    detail = models.CharField(max_length=250,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ImportBatch(models.Model):
    school = models.ForeignKey(School,on_delete=models.PROTECT)
    token = models.UUIDField(default=uuid.uuid4,unique=True)
    file_hash = models.CharField(max_length=64)
    state = models.CharField(max_length=12,default='preview',choices=[('preview','Пешнамоиш'),('committed','Сабтшуда')])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class LoginAttempt(models.Model):
    key = models.CharField(max_length=64,unique=True)
    failures = models.PositiveSmallIntegerField(default=0)
    window_start = models.DateTimeField()
