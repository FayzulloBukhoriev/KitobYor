import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from django.db.models import Q

class School(models.Model):
    name=models.CharField(max_length=180)
    code=models.CharField(max_length=24,unique=True)
    academic_year=models.CharField(max_length=9,default='2026-2027')
    def __str__(self):return self.name

class Membership(models.Model):
    ROLES=[('admin','Маъмури мактаб'),('librarian','Китобдор'),('accountant','Муҳосиб'),('viewer','Роҳбар')]
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='membership')
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    role=models.CharField(max_length=20,choices=ROLES,default='librarian')
    def __str__(self):return f'{self.user} / {self.school}'

class Student(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    code=models.CharField(max_length=40)
    full_name=models.CharField(max_length=200)
    grade=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(11)])
    group=models.CharField(max_length=8,default='А')
    address=models.CharField(max_length=250)
    active=models.BooleanField(default=True)
    class Meta:
        ordering=['grade','group','full_name']
        constraints=[models.UniqueConstraint(fields=['school','code'],name='student_school_code'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='student_grade_range')]
    def __str__(self):return f'{self.full_name} ({self.grade}-{self.group})'

class Edition(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    title=models.CharField(max_length=180)
    grade=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(11)])
    language=models.CharField(max_length=40,default='Тоҷикӣ')
    year=models.PositiveSmallIntegerField(validators=[MinValueValidator(1900),MaxValueValidator(2100)])
    code=models.CharField(max_length=60)
    publisher=models.CharField(max_length=120,blank=True)
    available=models.PositiveIntegerField(default=0)
    damaged=models.PositiveIntegerField(default=0)
    fee=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    tariff_year=models.CharField(max_length=9,default='2026-2027')
    approved=models.BooleanField(default=False)
    class Meta:
        ordering=['grade','title','-year']
        constraints=[models.UniqueConstraint(fields=['school','code'],name='edition_school_code'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='edition_grade_range'),models.CheckConstraint(condition=Q(fee__gte=0),name='edition_fee_positive')]
    def __str__(self):return f'{self.title} / {self.year} / {self.code}'

class Kit(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    name=models.CharField(max_length=120)
    grade=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(11)])
    language=models.CharField(max_length=40,default='Тоҷикӣ')
    academic_year=models.CharField(max_length=9,default='2026-2027')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['school','grade','language','academic_year'],name='one_class_kit'),models.CheckConstraint(condition=Q(grade__gte=1,grade__lte=11),name='kit_grade_range')]
    def __str__(self):return self.name

class KitItem(models.Model):
    kit=models.ForeignKey(Kit,on_delete=models.CASCADE,related_name='items')
    label=models.CharField(max_length=180)
    preferred=models.ForeignKey(Edition,on_delete=models.PROTECT,related_name='+')
    alternatives=models.ManyToManyField(Edition,blank=True,related_name='+')
    position=models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering=['position','id']
        constraints=[models.UniqueConstraint(fields=['kit','label'],name='kit_unique_label')]

class Invoice(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    student=models.ForeignKey(Student,on_delete=models.PROTECT)
    academic_year=models.CharField(max_length=9)
    token=models.UUIDField(default=uuid.uuid4,unique=True)
    reference=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    total=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    paid=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-id']
        constraints=[models.CheckConstraint(condition=Q(total__gte=0,paid__gte=0,paid__lte=models.F('total')),name='invoice_money_range')]
    @property
    def balance(self):return self.total-self.paid
    @property
    def number(self):return f'KY-{self.pk:08d}'

class IssueLine(models.Model):
    invoice=models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name='lines')
    student=models.ForeignKey(Student,on_delete=models.PROTECT)
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    kit_item=models.ForeignKey(KitItem,on_delete=models.PROTECT,null=True)
    title_snapshot=models.CharField(max_length=180)
    year_snapshot=models.PositiveSmallIntegerField()
    fee_snapshot=models.DecimalField(max_digits=10,decimal_places=2)
    returned_at=models.DateTimeField(null=True,blank=True)
    condition=models.CharField(max_length=12,choices=[('issued','Дода'),('good','Солим'),('damaged','Осебдида')],default='issued')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['student','kit_item'],condition=Q(returned_at__isnull=True),name='one_active_kit_item'),models.CheckConstraint(condition=Q(fee_snapshot__gte=0),name='line_fee_positive')]

class Payment(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    invoice=models.ForeignKey(Invoice,on_delete=models.PROTECT,related_name='payments')
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    receipt=models.CharField(max_length=120)
    note=models.CharField(max_length=250)
    token=models.UUIDField(default=uuid.uuid4,unique=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['school','receipt'],name='unique_payment_receipt'),models.CheckConstraint(condition=Q(amount__gt=0),name='payment_amount_positive')]

class StockMovement(models.Model):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT,related_name='movements')
    quantity=models.IntegerField()
    kind=models.CharField(max_length=20)
    note=models.CharField(max_length=250)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)

class AuditEvent(models.Model):
    school=models.ForeignKey(School,on_delete=models.PROTECT)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    action=models.CharField(max_length=60)
    object_id=models.CharField(max_length=80)
    detail=models.CharField(max_length=250,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class LoginAttempt(models.Model):
    key=models.CharField(max_length=64,unique=True)
    failures=models.PositiveSmallIntegerField(default=0)
    window_start=models.DateTimeField()
