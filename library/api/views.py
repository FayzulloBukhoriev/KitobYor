from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from library.models import Student,Edition,Kit,Invoice
from library import services
from .serializers import *

def validated(cls,data):
    s=cls(data=data);s.is_valid(raise_exception=True);return s.validated_data
class Students(generics.ListAPIView):
    serializer_class=StudentRead
    def get_queryset(self):
        qs=Student.objects.filter(school=self.request.school).prefetch_related('enrollments')
        if q:=self.request.query_params.get('q'):qs=qs.filter(full_name__icontains=q)
        if grade:=self.request.query_params.get('grade'):
            try:grade=int(grade)
            except ValueError:raise services.DomainError('Синф бояд рақам бошад.')
            qs=qs.filter(enrollments__academic_year=self.request.school.academic_year,enrollments__grade=grade)
        return qs
    def post(self,request):
        obj=services.add_student(user=request.user,school=request.school,**validated(StudentWrite,request.data))
        return Response(StudentRead(obj).data,status=201)
class Editions(generics.ListAPIView):
    serializer_class=EditionRead
    def get_queryset(self):
        qs=Edition.objects.filter(book__school=self.request.school).select_related('book','stock').prefetch_related('tariffs')
        if q:=self.request.query_params.get('q'):qs=qs.filter(book__title__icontains=q)
        return qs
    def post(self,request):
        obj=services.create_catalog(user=request.user,school=request.school,**validated(CatalogWrite,request.data))
        return Response(EditionRead(obj).data,status=201)
class StockIntake(APIView):
    def post(self,request,pk):
        obj=services.intake(user=request.user,school=request.school,edition_id=pk,**validated(IntakeWrite,request.data))
        return Response({'edition_id':pk,'available':obj.available,'damaged':obj.damaged})
class TariffSet(APIView):
    write_roles=('admin','accountant')
    def post(self,request,pk):
        obj=services.set_tariff(user=request.user,school=request.school,edition_id=pk,**validated(TariffWrite,request.data))
        return Response({'id':obj.pk,'fee':str(obj.fee),'academic_year':obj.academic_year,'approved':obj.approved})
class Kits(generics.ListAPIView):
    serializer_class=KitRead
    def get_queryset(self):return Kit.objects.filter(school=self.request.school).prefetch_related('items__alternatives')
    def post(self,request):
        obj=services.create_kit(user=request.user,school=request.school,**validated(KitWrite,request.data))
        return Response(KitRead(obj).data,status=201)
class Preview(APIView):
    def get(self,request):return Response(services.preview_issue(request.school,**validated(PreviewWrite,request.query_params)))
class IssueConfirm(APIView):
    def post(self,request):
        inv=services.confirm_issue(user=request.user,school=request.school,**validated(IssueWrite,request.data))
        return Response(InvoiceRead(inv).data,status=200)
class Invoices(generics.ListAPIView):
    serializer_class=InvoiceRead
    def get_queryset(self):return Invoice.objects.filter(school=self.request.school).select_related('loan__student').prefetch_related('loan__lines')
class InvoiceDetail(generics.RetrieveAPIView):
    serializer_class=InvoiceRead
    def get_queryset(self):return Invoice.objects.filter(school=self.request.school).select_related('loan__student').prefetch_related('loan__lines')
class Payments(APIView):
    write_roles=('admin','accountant')
    def post(self,request,pk):
        obj=services.record_payment(user=request.user,school=request.school,invoice_id=pk,**validated(PaymentWrite,request.data))
        return Response(PaymentRead(obj).data,status=200)
class Returns(APIView):
    def post(self,request,pk):
        obj=services.close_lines(user=request.user,school=request.school,loan_id=pk,**validated(ReturnWrite,request.data))
        return Response({'loan_id':obj.pk,'lines':LineRead(obj.lines.all(),many=True).data,'invoice_balance':str(obj.invoice.balance)})

class Catalog(generics.ListAPIView):
    serializer_class=EditionRead
    def get_queryset(self):return Edition.objects.filter(book__school=self.request.school).select_related('book','stock').prefetch_related('tariffs')
    def post(self,request):
        obj=services.save_inventory(user=request.user,school=request.school,**validated(InventoryWrite,request.data))
        return Response(EditionRead(obj).data,status=201)
class CatalogEdit(APIView):
    def post(self,request,pk):
        obj=services.save_inventory(user=request.user,school=request.school,edition_id=pk,**validated(InventoryWrite,request.data))
        return Response(EditionRead(obj).data)
class CatalogIssueConfirm(APIView):
    def post(self,request):
        inv=services.confirm_catalog_issue(user=request.user,school=request.school,**validated(CatalogIssueWrite,request.data))
        return Response(InvoiceRead(inv).data)
class CashPaid(APIView):
    write_roles=('admin','accountant')
    def post(self,request,pk):
        inv=services.mark_cash_paid(user=request.user,school=request.school,invoice_id=pk)
        return Response(InvoiceRead(inv).data)
