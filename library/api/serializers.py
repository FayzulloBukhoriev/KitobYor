from decimal import Decimal
from rest_framework import serializers
from library.models import Student,Edition,Kit,Invoice,Payment,LoanLine

class StudentRead(serializers.ModelSerializer):
    enrollments=serializers.SerializerMethodField()
    class Meta: model=Student;fields=['id','code','full_name','address','parent_name','parent_phone','active','enrollments']
    def get_enrollments(self,obj):
        return [{'academic_year':e.academic_year,'grade':e.grade,'group':e.group,'language':e.language} for e in obj.enrollments.all()]

class StudentWrite(serializers.Serializer):
    code=serializers.CharField(max_length=40,required=False)
    full_name=serializers.CharField(max_length=200)
    address=serializers.CharField(max_length=250)
    parent_name=serializers.CharField(max_length=160,required=False,allow_blank=True)
    parent_phone=serializers.CharField(max_length=20,required=False,allow_blank=True)
    grade=serializers.IntegerField(min_value=1,max_value=11)
    group=serializers.CharField(max_length=8)
    language=serializers.CharField(max_length=40,default='Тоҷикӣ')

class CatalogWrite(serializers.Serializer):
    book_code=serializers.CharField(max_length=60)
    title=serializers.CharField(max_length=180)
    grade=serializers.IntegerField(min_value=1,max_value=11)
    language=serializers.CharField(max_length=40,default='Тоҷикӣ')
    edition_code=serializers.CharField(max_length=60)
    year=serializers.IntegerField(min_value=1900,max_value=2100)
    publisher=serializers.CharField(max_length=120,required=False,allow_blank=True)
    isbn=serializers.CharField(max_length=20,required=False,allow_blank=True)

class EditionRead(serializers.ModelSerializer):
    title=serializers.CharField(source='book.title')
    grade=serializers.IntegerField(source='book.grade')
    language=serializers.CharField(source='book.language')
    available=serializers.SerializerMethodField()
    damaged=serializers.SerializerMethodField()
    tariffs=serializers.SerializerMethodField()
    class Meta: model=Edition;fields=['id','book_id','title','grade','language','code','year','publisher','isbn','available','damaged','tariffs']
    def get_available(self,obj): return obj.stock.available if hasattr(obj,'stock') else 0
    def get_damaged(self,obj): return obj.stock.damaged if hasattr(obj,'stock') else 0
    def get_tariffs(self,obj):return [{'academic_year':t.academic_year,'fee':str(t.fee),'approved':t.approved} for t in obj.tariffs.all()]

class KitEntryWrite(serializers.Serializer):
    preferred_id=serializers.IntegerField(min_value=1)
    alternative_ids=serializers.ListField(child=serializers.IntegerField(min_value=1),default=[],max_length=20)
class KitWrite(serializers.Serializer):
    name=serializers.CharField(max_length=120)
    grade=serializers.IntegerField(min_value=1,max_value=11)
    language=serializers.CharField(max_length=40,default='Тоҷикӣ')
    items=KitEntryWrite(many=True,min_length=5,max_length=15)
class KitRead(serializers.ModelSerializer):
    items=serializers.SerializerMethodField()
    class Meta:model=Kit;fields=['id','name','grade','language','academic_year','items']
    def get_items(self,obj):return [{'id':i.pk,'label':i.label,'preferred_id':i.preferred_id,'alternative_ids':[e.pk for e in i.alternatives.all()]} for i in obj.items.all()]

class ChoiceWrite(serializers.Serializer):
    kit_item_id=serializers.IntegerField(min_value=1)
    edition_id=serializers.IntegerField(min_value=1)
class IssueWrite(serializers.Serializer):
    student_id=serializers.IntegerField(min_value=1)
    kit_id=serializers.IntegerField(min_value=1)
    choices=ChoiceWrite(many=True,min_length=1,max_length=15)
    token=serializers.UUIDField()
    expected_total=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=0)
    allow_partial=serializers.BooleanField(default=False)
class PreviewWrite(serializers.Serializer):
    student_id=serializers.IntegerField(min_value=1)
    kit_id=serializers.IntegerField(min_value=1)
class IntakeWrite(serializers.Serializer):
    quantity=serializers.IntegerField(min_value=1,max_value=100000)
    note=serializers.CharField(max_length=250)
class TariffWrite(serializers.Serializer):
    fee=serializers.DecimalField(max_digits=10,decimal_places=2,min_value=0)
    note=serializers.CharField(max_length=250)
    approved=serializers.BooleanField()
class PaymentWrite(serializers.Serializer):
    amount=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=Decimal('0.01'))
    receipt=serializers.CharField(max_length=120)
    note=serializers.CharField(max_length=250)
    token=serializers.UUIDField()
class ReturnEntry(serializers.Serializer):
    line_id=serializers.IntegerField(min_value=1)
    state=serializers.ChoiceField(choices=['returned','damaged','lost'])
class ReturnWrite(serializers.Serializer):
    lines=ReturnEntry(many=True,min_length=1,max_length=15)
class LineRead(serializers.ModelSerializer):
    class Meta:model=LoanLine;fields=['id','edition_id','kit_item_id','title_snapshot','year_snapshot','fee_snapshot','state','closed_at']
class InvoiceRead(serializers.ModelSerializer):
    student_id=serializers.IntegerField(source='loan.student_id')
    full_name=serializers.CharField(source='loan.student.full_name')
    lines=LineRead(source='loan.lines',many=True)
    balance=serializers.DecimalField(max_digits=12,decimal_places=2,read_only=True)
    number=serializers.CharField(read_only=True)
    payment_number=serializers.CharField(read_only=True)
    class Meta:model=Invoice;fields=['id','number','payment_number','reference','loan_id','student_id','full_name','total','paid','balance','created_at','lines']
class PaymentRead(serializers.ModelSerializer):
    class Meta:model=Payment;fields=['id','invoice_id','amount','receipt','note','created_at']

class InventoryWrite(serializers.Serializer):
    title=serializers.CharField(max_length=180)
    grade=serializers.IntegerField(min_value=1,max_value=11)
    year=serializers.IntegerField(min_value=1900,max_value=2100)
    quantity=serializers.IntegerField(min_value=0,max_value=100000)
    fee=serializers.DecimalField(max_digits=10,decimal_places=2,min_value=0)
class CatalogIssueWrite(serializers.Serializer):
    student_id=serializers.IntegerField(min_value=1)
    edition_ids=serializers.ListField(child=serializers.IntegerField(min_value=1),min_length=1,max_length=60)
    expected_total=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=0)
    token=serializers.UUIDField()
