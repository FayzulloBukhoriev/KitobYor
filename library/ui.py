"""Server-rendered school workspace. Every data query is scoped to request.school."""
import csv
from decimal import Decimal
from uuid import uuid4
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .permissions import school_required
from .models import Student, Enrollment, Edition, Stock, LoanLine, Invoice, Kit, AuditEvent
from .forms import StudentForm, CatalogForm, IntakeForm, TariffForm, KitForm, PaymentForm, ImportForm
from . import services, importing
from .api.serializers import IssueWrite
from rest_framework.exceptions import ValidationError as APIValidationError


def page(request,template,**context):
    context.update(can_library=request.member.role in ('admin','librarian'),can_finance=request.member.role in ('admin','accountant'),grades=range(1,12))
    return render(request,'library/'+template+'.html',context)

def error(form,exc):
    form.add_error(None,'; '.join(exc.messages) if isinstance(exc,ValidationError) else str(exc))

def student_query(request):
    qs=Student.objects.filter(school=request.school).prefetch_related('enrollments')
    enrollment_filters={'enrollments__academic_year':request.school.academic_year}
    q=request.GET.get('q','').strip();grade=request.GET.get('grade','');group=request.GET.get('group','').strip()
    if q:qs=qs.filter(Q(full_name__icontains=q)|Q(code__icontains=q))
    if grade.isdigit() and 1<=int(grade)<=11:enrollment_filters['enrollments__grade']=int(grade)
    if group:enrollment_filters['enrollments__group']=group
    return qs.filter(**enrollment_filters).distinct()

def paginate(request,qs):return Paginator(qs,20).get_page(request.GET.get('page'))

@school_required()
def dashboard(request):
    school=request.school
    money=Invoice.objects.filter(school=school,loan__academic_year=school.academic_year).aggregate(total=Sum('total'),paid=Sum('paid'))
    total,paid=money['total'] or Decimal('0.00'),money['paid'] or Decimal('0.00')
    stats={'students':Student.objects.filter(school=school,active=True,enrollments__academic_year=school.academic_year).count(),'available':Stock.objects.filter(edition__book__school=school).aggregate(n=Sum('available'))['n'] or 0,'issued':LoanLine.objects.filter(loan__school=school,state='issued').count(),'total':total,'paid':paid,'debt':total-paid}
    return page(request,'dashboard',active='dashboard',title='Пештахта',stats=stats,recent=Invoice.objects.filter(school=school).select_related('loan__student')[:5],low=Edition.objects.filter(book__school=school,stock__available__lt=5).select_related('book','stock')[:5],activity=AuditEvent.objects.filter(school=school).select_related('user').order_by('-id')[:5])

@school_required()
def students(request):
    return page(request,'students',active='students',title='Хонандагон',rows=paginate(request,student_query(request)),q=request.GET.get('q',''),grade=request.GET.get('grade',''),group=request.GET.get('group',''))

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def student_form(request,pk=None):
    student=get_object_or_404(Student,school=request.school,pk=pk) if pk else None
    initial={}
    if student:
        en=services.enrollment(student,request.school)
        initial=dict(code=student.code,full_name=student.full_name,address=student.address,grade=en.grade,group=en.group,language=en.language)
    form=StudentForm(request.POST if request.method=='POST' else None,initial=initial)
    if request.method=='POST' and form.is_valid():
        try:
            if student:services.update_student(user=request.user,school=request.school,student_id=student.pk,**form.cleaned_data)
            else:services.add_student(user=request.user,school=request.school,**form.cleaned_data)
            messages.success(request,'Маълумоти хонанда сабт шуд.');return redirect('students')
        except (services.DomainError,ValidationError) as exc:error(form,exc)
    return page(request,'form',active='students',title='Таҳрири хонанда' if student else 'Хонандаи нав',form=form,subtitle='Маълумоти шахсӣ ва синфи соли ҷорӣ.',back='students')

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def student_import(request):
    preview=request.session.get('student_import')
    if preview and preview.get('school_id')!=request.school.pk:
        request.session.pop('student_import',None);preview=None
    form=ImportForm(request.POST if request.method=='POST' and request.POST.get('action')!='commit' else None,request.FILES or None)
    checked=None
    if request.method=='POST' and request.POST.get('action')=='commit':
        try:
            if not preview or preview.get('school_id')!=request.school.pk or request.POST.get('token')!=preview['token']:raise services.DomainError('Пешнамоиш кӯҳна шудааст. Рӯйхатро аз нав кушоед.')
            n=importing.commit_import(user=request.user,school=request.school,rows=preview['rows'],token=preview['token'],file_hash=preview['hash'])
            request.session.pop('student_import',None);messages.success(request,f'{n} хонанда илова шуд.');return redirect('students')
        except services.DomainError as exc:messages.error(request,str(exc))
    elif request.method=='POST' and form.is_valid():
        try:
            rows,digest=importing.parse_upload(form.cleaned_data.get('file'),form.cleaned_data.get('pasted',''))
            preview={'rows':rows,'hash':digest,'token':str(uuid4()),'school_id':request.school.pk}
            request.session['student_import']=preview
        except services.DomainError as exc:error(form,exc)
    if preview:checked,valid=importing.validate_rows(preview['rows'],request.school)
    else:valid=[]
    return page(request,'import',active='students',title='Воридкунии оммавӣ',form=form,preview=checked,valid_count=len(valid),has_errors=checked is not None and len(valid)!=len(checked),token=preview['token'] if preview else '')

@school_required()
def import_template(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="KitobYor-students.csv"'
    response.write('\ufeff');writer=csv.writer(response);writer.writerow(importing.HEADERS);writer.writerow(['NEW001','Хонандаи намунавӣ','5','А','Суроғаи намунавӣ','Тоҷикӣ'])
    return response

@school_required()
def inventory(request):
    qs=Edition.objects.filter(book__school=request.school).select_related('book','stock').prefetch_related('tariffs')
    q=request.GET.get('q','').strip();grade=request.GET.get('grade','')
    if q:qs=qs.filter(Q(book__title__icontains=q)|Q(code__icontains=q)|Q(book__code__icontains=q))
    if grade.isdigit() and 1<=int(grade)<=11:qs=qs.filter(book__grade=int(grade))
    rows=paginate(request,qs.order_by('book__grade','book__title','-year','id'))
    for ed in rows:ed.current_tariff=next((t for t in ed.tariffs.all() if t.academic_year==request.school.academic_year),None)
    return page(request,'inventory',active='inventory',title='Анбори китобҳо',rows=rows,q=q,grade=grade)

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def catalog_form(request):
    form=CatalogForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        try:
            ed=services.create_catalog(user=request.user,school=request.school,**form.cleaned_data)
            messages.success(request,'Нашр илова шуд. Ҳоло шумораи нусхаҳоро ворид кунед.');return redirect('edition_detail',pk=ed.pk)
        except (services.DomainError,ValidationError) as exc:error(form,exc)
    return page(request,'form',active='inventory',title='Иловаи китоб ё нашр',subtitle='Барои ҳар нашр бақия ва тариф ҷудо нигоҳ дошта мешавад.',form=form,back='inventory')

@school_required()
@require_http_methods(['GET','POST'])
def edition_detail(request,pk):
    ed=get_object_or_404(Edition.objects.select_related('book','stock'),book__school=request.school,pk=pk)
    tariff=ed.tariffs.filter(academic_year=request.school.academic_year).first()
    intake=IntakeForm(prefix='intake');pricing=TariffForm(prefix='tariff',initial={'fee':tariff.fee,'note':tariff.note,'approved':tariff.approved} if tariff else {})
    if request.method=='POST':
        action=request.POST.get('action')
        if action=='intake':
            intake=IntakeForm(request.POST,prefix='intake')
            if intake.is_valid():
                try:services.intake(user=request.user,school=request.school,edition_id=ed.pk,**intake.cleaned_data);messages.success(request,'Нусхаҳо ба анбор ворид шуданд.');return redirect('edition_detail',pk=pk)
                except services.DomainError as exc:error(intake,exc)
        elif action=='tariff':
            pricing=TariffForm(request.POST,prefix='tariff')
            if pricing.is_valid():
                try:services.set_tariff(user=request.user,school=request.school,edition_id=ed.pk,**pricing.cleaned_data);messages.success(request,'Тариф сабт шуд.');return redirect('edition_detail',pk=pk)
                except (services.DomainError,ValidationError) as exc:error(pricing,exc)
        else:messages.error(request,'Амали номаълум.')
    return page(request,'edition',active='inventory',title=ed.book.title,ed=ed,tariff=tariff,intake=intake,pricing=pricing,movements=ed.movements.select_related('created_by').order_by('-id')[:20])

@school_required()
def kits(request):
    return page(request,'kits',active='kits',title='Маҷмӯаҳои синф',kits=Kit.objects.filter(school=request.school,academic_year=request.school.academic_year).prefetch_related('items__preferred__book','items__alternatives').order_by('grade','language'))

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def kit_form(request):
    form=KitForm(request.POST if request.method=='POST' else None,school=request.school)
    if request.method=='POST' and form.is_valid():
        try:
            services.create_kit(user=request.user,school=request.school,name=form.cleaned_data['name'],grade=form.cleaned_data['grade'],language=form.cleaned_data['language'],items=form.cleaned_data['items'])
            messages.success(request,'Маҷмӯа омода шуд. Барои хонандагони ин синф худкор пешниҳод мешавад.');return redirect('kits')
        except (services.DomainError,ValidationError) as exc:error(form,exc)
    pairs=[(form[f'edition_{n}'],form[f'alternatives_{n}']) for n in range(1,16)]
    return page(request,'kit_form',active='kits',title='Маҷмӯаи нав',form=form,pairs=pairs)

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def issue(request):
    student=None;kit=None;preview=None
    raw=request.POST.get('student_id') if request.method=='POST' else request.GET.get('student')
    if raw:
        student=get_object_or_404(Student,school=request.school,pk=raw if str(raw).isdigit() else 0)
        try:
            en=services.enrollment(student,request.school)
            kit=Kit.objects.filter(school=request.school,grade=en.grade,language=en.language,academic_year=request.school.academic_year).first()
            if not kit:messages.warning(request,'Барои синф ва забони ин хонанда маҷмӯа ҳанӯз сохта нашудааст.')
            else:
                if request.method=='POST':
                    choices=[]
                    for item in kit.items.all():
                        value=request.POST.get(f'choice_{item.pk}','')
                        if value:choices.append({'kit_item_id':item.pk,'edition_id':value})
                    data=IssueWrite(data={'student_id':student.pk,'kit_id':kit.pk,'choices':choices,'expected_total':request.POST.get('expected_total'),'token':request.POST.get('token'),'allow_partial':request.POST.get('allow_partial')=='on'})
                    data.is_valid(raise_exception=True)
                    inv=services.confirm_issue(user=request.user,school=request.school,**data.validated_data)
                    messages.success(request,'Китобҳо дода шуданд. Ҳисоби иҷора омода аст.');return redirect('invoice_detail',pk=inv.pk)
                preview=services.preview_issue(request.school,student.pk,kit.pk)
        except (services.DomainError,APIValidationError) as exc:
            messages.error(request,str(exc) if isinstance(exc,services.DomainError) else 'Интихоб ва маблағро санҷед. Ҳадди ақал як китоб лозим аст.')
            if kit:preview=services.preview_issue(request.school,student.pk,kit.pk)
    if preview:
        for row in preview['items']:
            row['ready_choices']=[c for c in row['choices'] if c['available']>0 and c['approved']]
    return page(request,'issue',active='issue',title='Додани китоб',students=paginate(request,student_query(request).filter(active=True)),student=student,kit=kit,preview=preview,token=str(uuid4()),q=request.GET.get('q',''),grade=request.GET.get('grade',''),group=request.GET.get('group',''))

@school_required()
def invoices(request):
    qs=Invoice.objects.filter(school=request.school).select_related('loan__student')
    q=request.GET.get('q','').strip();status=request.GET.get('status','')
    if q:qs=qs.filter(Q(loan__student__full_name__icontains=q)|Q(loan__student__code__icontains=q))
    if status=='paid':qs=qs.filter(paid=F('total'))
    elif status=='unpaid':qs=qs.filter(paid=0,total__gt=0)
    elif status=='partial':qs=qs.filter(paid__gt=0,paid__lt=F('total'))
    return page(request,'invoices',active='invoices',title='Ҳисобҳои иҷора',rows=paginate(request,qs),q=q,status=status)

@school_required()
@require_http_methods(['GET','POST'])
def invoice_detail(request,pk):
    inv=get_object_or_404(Invoice.objects.select_related('loan__student'),school=request.school,pk=pk)
    payment=PaymentForm(initial={'amount':inv.balance,'token':uuid4()})
    if request.method=='POST':
        if request.POST.get('action')=='payment':
            payment=PaymentForm(request.POST)
            if payment.is_valid():
                try:
                    services.record_payment(user=request.user,school=request.school,invoice_id=inv.pk,**payment.cleaned_data)
                    messages.success(request,'Пардохт сабт шуд.');return redirect('invoice_detail',pk=pk)
                except services.DomainError as exc:error(payment,exc)
        elif request.POST.get('action')=='return':
            try:
                lines=[]
                for line in inv.loan.lines.all():
                    if request.POST.get(f'return_{line.pk}'):lines.append({'line_id':line.pk,'state':request.POST.get(f'state_{line.pk}')})
                services.close_lines(user=request.user,school=request.school,loan_id=inv.loan_id,lines=lines)
                messages.success(request,'Ҳолати китобҳо сабт шуд. Бақияи қарз тағйир наёфт.');return redirect('invoice_detail',pk=pk)
            except services.DomainError as exc:messages.error(request,str(exc))
        else:messages.error(request,'Амали номаълум.')
    return page(request,'invoice',active='invoices',title=inv.number,inv=inv,lines=inv.loan.lines.select_related('edition'),payments=inv.payments.select_related('created_by').order_by('-id'),payment=payment)

@school_required()
def returns(request):
    qs=Invoice.objects.filter(school=request.school,loan__lines__state='issued').distinct().select_related('loan__student')
    q=request.GET.get('q','').strip()
    if q:qs=qs.filter(Q(loan__student__full_name__icontains=q)|Q(loan__student__code__icontains=q))
    return page(request,'returns',active='returns',title='Баргардонидани китоб',rows=paginate(request,qs),q=q)

@school_required()
def reports(request):
    totals=Invoice.objects.filter(school=request.school).aggregate(total=Sum('total'),paid=Sum('paid'))
    return page(request,'reports',active='reports',title='Ҳисобот',total=totals['total'] or 0,paid=totals['paid'] or 0)

def csv_safe(value):
    value=str(value)
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value

@school_required()
def export(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="KitobYor-report.csv"';response.write('\ufeff');writer=csv.writer(response)
    kind=request.GET.get('kind','invoices')
    if kind=='stock':
        writer.writerow(['Китоб','Синф','Нашр','Рамзи нашр','Дастрас','Осебдида'])
        for ed in Edition.objects.filter(book__school=request.school).select_related('book','stock'):
            writer.writerow([csv_safe(ed.book.title),ed.book.grade,ed.year,csv_safe(ed.code),ed.stock.available,ed.stock.damaged])
    else:
        writer.writerow(['Ҳисоб','Хонанда','Китоб','Соли нашр','Иҷора','Ҳолат','Ҳамагӣ','Пардохт','Қарз','Истинод'])
        qs=Invoice.objects.filter(school=request.school).select_related('loan__student').prefetch_related('loan__lines')
        if kind=='debt':qs=qs.filter(paid__lt=F('total'))
        for inv in qs:
            for line in inv.loan.lines.all():
                if kind=='outstanding' and line.state!='issued':continue
                writer.writerow([inv.number,csv_safe(inv.loan.student.full_name),csv_safe(line.title_snapshot),line.year_snapshot,line.fee_snapshot,line.get_state_display(),inv.total,inv.paid,inv.balance,str(inv.reference)])
    return response
