"""Server-rendered school workspace. Every data query is scoped to request.school."""
import csv
from decimal import Decimal
from uuid import uuid4,UUID
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .permissions import school_required
from .models import Student, Enrollment, Edition, Stock, LoanLine, Invoice, Kit, AuditEvent, SmsNotification
from .forms import StudentForm, CatalogForm, IntakeForm, TariffForm, KitForm, PaymentForm, ImportForm, GROUPS, normalize_group
from . import services, importing
from .api.serializers import IssueWrite
from rest_framework.exceptions import ValidationError as APIValidationError


def page(request,template,**context):
    context.update(can_library=request.member.role in ('admin','librarian'),can_finance=request.member.role in ('admin','accountant'),grades=range(1,12),groups=GROUPS)
    return render(request,'library/'+template+'.html',context)

def error(form,exc):
    form.add_error(None,'; '.join(exc.messages) if isinstance(exc,ValidationError) else str(exc))

def student_query(request):
    qs=Student.objects.filter(school=request.school).prefetch_related('enrollments')
    enrollment_filters={'enrollments__academic_year':request.school.academic_year}
    q=request.GET.get('q','').strip();grade=request.GET.get('grade','');group=normalize_group(request.GET.get('group',''))
    if q:qs=qs.filter(Q(full_name__icontains=q)|Q(code__icontains=q))
    if grade in {str(n) for n in range(1,12)}:enrollment_filters['enrollments__grade']=int(grade)
    if group:enrollment_filters['enrollments__group']=group
    return qs.filter(**enrollment_filters).distinct()

def paginate(request,qs):return Paginator(qs,20).get_page(request.GET.get('page'))

@school_required()
def dashboard(request):
    school=request.school
    money=Invoice.objects.filter(school=school,loan__academic_year=school.academic_year).aggregate(total=Sum('total'),paid=Sum('paid'))
    total,paid=money['total'] or Decimal('0.00'),money['paid'] or Decimal('0.00')
    stats={'students':Student.objects.filter(school=school,active=True,enrollments__academic_year=school.academic_year).count(),'available':Stock.objects.filter(edition__book__school=school).aggregate(n=Sum('available'))['n'] or 0,'issued':LoanLine.objects.filter(loan__school=school,state='issued').count(),'total':total,'paid':paid,'paid_count':Invoice.objects.filter(school=school,loan__academic_year=school.academic_year,paid=F('total')).count(),'unpaid_count':Invoice.objects.filter(school=school,loan__academic_year=school.academic_year,paid__lt=F('total')).count(),'paid_amount':paid}
    return page(request,'dashboard',active='dashboard',title='Пештахта',stats=stats,recent=Invoice.objects.filter(school=school).select_related('loan__student')[:5],low=Edition.objects.filter(book__school=school,stock__available__lt=5).select_related('book','stock')[:5],activity=AuditEvent.objects.filter(school=school).select_related('user').order_by('-id')[:5])

@school_required()
def students(request):
    rows=paginate(request,student_query(request))
    latest={}
    for inv in Invoice.objects.filter(school=request.school,loan__student_id__in=[r.pk for r in rows],loan__academic_year=request.school.academic_year).select_related('loan').order_by('-id'):
        latest.setdefault(inv.loan.student_id,inv)
    for student in rows:student.latest_invoice=latest.get(student.pk)
    return page(request,'students',active='students',title='Хонандагон',rows=rows,q=request.GET.get('q',''),grade=request.GET.get('grade',''),group=normalize_group(request.GET.get('group','')))

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def student_form(request,pk=None):
    student=get_object_or_404(Student,school=request.school,pk=pk) if pk else None
    initial={}
    if student:
        en=services.enrollment(student,request.school)
        initial=dict(full_name=student.full_name,address=student.address,grade=en.grade,group=normalize_group(en.group),language=en.language,parent_name=student.parent_name,parent_phone=student.parent_phone)
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
    response.write('\ufeff');writer=csv.writer(response);writer.writerow(importing.HEADERS);writer.writerow(['Хонандаи намунавӣ','5','A','Суроғаи намунавӣ','Намояндаи намунавӣ','+992000000000'])
    return response

@school_required()
def inventory(request):
    qs=Edition.objects.filter(book__school=request.school).select_related('book','stock').prefetch_related('tariffs')
    q=request.GET.get('q','').strip();grade=request.GET.get('grade','')
    if q:qs=qs.filter(Q(book__title__icontains=q)|Q(code__icontains=q)|Q(book__code__icontains=q))
    if grade in {str(n) for n in range(1,12)}:qs=qs.filter(book__grade=int(grade))
    rows=paginate(request,qs.order_by('book__grade','book__title','-year','id'))
    for ed in rows:ed.current_tariff=next((t for t in ed.tariffs.all() if t.academic_year==request.school.academic_year),None)
    return page(request,'inventory',active='inventory',title='Анбори китобҳо',rows=rows,q=q,grade=grade)

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def catalog_form(request,pk=None):
    ed=get_object_or_404(Edition.objects.select_related('book','stock'),book__school=request.school,pk=pk) if pk else None
    initial={}
    if ed:
        tariff=ed.tariffs.filter(academic_year=request.school.academic_year).first()
        initial=dict(title=ed.book.title,grade=ed.book.grade,year=ed.year,quantity=ed.stock.available if hasattr(ed,'stock') else 0,fee=tariff.fee if tariff else 0,expected_revision=services.inventory_revision(ed))
    form=CatalogForm(request.POST if request.method=='POST' else None,initial=initial)
    form.fields['expected_revision'].required=bool(ed)
    if request.method=='POST' and form.is_valid():
        try:
            services.save_inventory(user=request.user,school=request.school,edition_id=ed.pk if ed else None,**form.cleaned_data)
            messages.success(request,'Маълумоти китоб иваз шуд.' if ed else 'Китоб, шумора ва нарх сабт шуданд.');return redirect('inventory')
        except (services.DomainError,ValidationError) as exc:error(form,exc)
    return page(request,'form',active='inventory',title='Иваз кардани китоб' if ed else 'Китоби нав',subtitle='Шумора — нусхаҳои ҳоло дар анбор. Нашри соли дигар нархи ҷудо дорад.',form=form,back='inventory')

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
            messages.success(request,'Маҷмӯа сабт шуд. Истифодаи он ихтиёрӣ аст.');return redirect('kits')
        except (services.DomainError,ValidationError) as exc:error(form,exc)
    pairs=[(form[f'edition_{n}'],form[f'alternatives_{n}']) for n in range(1,16)]
    return page(request,'kit_form',active='kits',title='Маҷмӯаи нав',form=form,pairs=pairs)

@school_required('admin','librarian')
@require_http_methods(['GET','POST'])
def issue(request):
    student=None;preview=None
    raw=request.POST.get('student_id') if request.method=='POST' else request.GET.get('student')
    if raw:
        student=get_object_or_404(Student,school=request.school,active=True,pk=int(raw) if str(raw).isascii() and str(raw).isdigit() and len(str(raw))<=18 else 0)
        try:
            if request.method=='POST':
                ids=[int(v) for v in request.POST.getlist('editions')]
                total=Decimal(request.POST.get('expected_total',''))
                inv=services.confirm_catalog_issue(user=request.user,school=request.school,student_id=student.pk,edition_ids=ids,token=UUID(request.POST.get('token','')),expected_total=total)
                messages.success(request,'Иҷора тасдиқ шуд. Рақами пардохт ва ҳолати SMS дар поён нишон дода шудаанд.');return redirect('invoice_detail',pk=inv.pk)
            preview=services.preview_catalog(request.school,student.pk)
        except (ValueError,ArithmeticError,services.DomainError) as exc:
            messages.error(request,str(exc) if isinstance(exc,services.DomainError) else 'Интихоби китобҳо ва маблағро санҷед.')
            try:preview=services.preview_catalog(request.school,student.pk)
            except services.DomainError:return redirect('students')
    if request.method=='POST' and preview:
        selected=set(request.POST.getlist('editions'))
        for row in preview['items']:
            chosen=next((c for c in row['choices'] if str(c['edition_id']) in selected and c['enabled']),None)
            if chosen and not row['already_held']:row['suggested']=chosen;row['selected']=True
    return page(request,'issue',active='issue',title='Додани китоб',students=paginate(request,student_query(request).filter(active=True)),student=student,preview=preview,token=str(uuid4()),q=request.GET.get('q',''),grade=request.GET.get('grade',''),group=normalize_group(request.GET.get('group','')))


def invoice_query(request):
    qs=Invoice.objects.filter(school=request.school).select_related('loan__student').prefetch_related('loan__student__enrollments').annotate(book_count=Count('loan__lines'))
    q=request.GET.get('q','').strip();status=request.GET.get('status','')
    if q.isascii() and q.isdigit() and q.startswith('10'):
        pk=q[2:]
        qs=qs.filter(pk=int(pk)) if pk.isascii() and pk.isdigit() and len(pk)<=18 else qs.none()
    elif q:qs=qs.filter(loan__student__full_name__icontains=q)
    if status=='paid':qs=qs.filter(paid=F('total'))
    elif status=='unpaid':qs=qs.filter(paid__lt=F('total'))
    grade=request.GET.get('grade','');group=normalize_group(request.GET.get('group',''))
    filters={}
    if grade in {str(n) for n in range(1,12)}:filters['loan__student__enrollments__grade']=int(grade)
    if group in 'ABCDE' and len(group)==1:filters['loan__student__enrollments__group']=group
    if filters:
        filters['loan__student__enrollments__academic_year']=F('loan__academic_year')
        qs=qs.filter(**filters)
    return qs.order_by('-id')

@school_required()
@require_http_methods(['GET','POST'])
def invoices(request):
    if request.method=='POST':
        try:
            services.mark_cash_paid(user=request.user,school=request.school,invoice_id=int(request.POST.get('invoice_id','0')))
            messages.success(request,'Қабули маблағи нақдӣ тасдиқ шуд.');return redirect(request.get_full_path())
        except (ValueError,services.DomainError) as exc:messages.error(request,str(exc) if isinstance(exc,services.DomainError) else 'Иҷора ёфт нашуд.')
    return page(request,'invoices',active='invoices',title='Иҷораҳо',rows=paginate(request,invoice_query(request)),q=request.GET.get('q',''),status=request.GET.get('status',''),grade=request.GET.get('grade',''),group=normalize_group(request.GET.get('group','')))

@school_required()
@require_http_methods(['GET','POST'])
def invoice_detail(request,pk):
    inv=get_object_or_404(Invoice.objects.select_related('loan__student').prefetch_related('loan__student__enrollments'),school=request.school,pk=pk)
    if request.method=='POST':
        try:
            if request.POST.get('action')!='paid':raise services.DomainError('Амали номаълум.')
            services.mark_cash_paid(user=request.user,school=request.school,invoice_id=inv.pk)
            messages.success(request,'Пардохти нақдӣ сабт шуд.');return redirect('invoice_detail',pk=pk)
        except services.DomainError as exc:messages.error(request,str(exc))
    return page(request,'invoice',active='invoices',title='Иҷораи китоб',inv=inv,lines=inv.loan.lines.all(),payments=inv.payments.select_related('created_by').order_by('-id'),notification=SmsNotification.objects.filter(invoice=inv).first())

@school_required()
def reports(request):
    qs=Invoice.objects.filter(school=request.school)
    totals=qs.aggregate(total=Sum('total'),paid=Sum('paid'))
    return page(request,'reports',active='reports',title='Ҳисобот',total=totals['total'] or 0,paid=totals['paid'] or 0,paid_count=qs.filter(paid=F('total')).count(),unpaid_count=qs.filter(paid__lt=F('total')).count(),rentals=qs.count(),book_count=LoanLine.objects.filter(loan__school=request.school).count())

def csv_safe(value):
    value=str(value)
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value

@school_required()
def export(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="KitobYor-report.csv"';response.write('\ufeff');writer=csv.writer(response)
    kind=request.GET.get('kind','invoices')
    if kind=='stock':
        writer.writerow(['Китоб','Синф','Соли нашр','Шумора дар анбор','Нархи иҷора'])
        for ed in Edition.objects.filter(book__school=request.school).select_related('book','stock').prefetch_related('tariffs'):
            tariff=next((t for t in ed.tariffs.all() if t.academic_year==request.school.academic_year),None)
            writer.writerow([csv_safe(ed.book.title),ed.book.grade,ed.year,ed.stock.available if hasattr(ed,'stock') else 0,tariff.fee if tariff else ''])
    else:
        writer.writerow(['Рақами пардохт (дохилӣ)','Хонанда','Синф','Гурӯҳ','Шумораи китобҳо','Китобҳо','Маблағ','Ҳолати пардохт','Сана'])
        qs=invoice_query(request).prefetch_related('loan__lines')
        if kind=='paid':qs=qs.filter(paid=F('total'))
        if kind=='unpaid':qs=qs.filter(paid__lt=F('total'))
        for inv in qs:
            en=next((e for e in inv.loan.student.enrollments.all() if e.academic_year==inv.loan.academic_year),None)
            books='; '.join(f'{line.title_snapshot} ({line.year_snapshot})' for line in inv.loan.lines.all())
            writer.writerow([inv.payment_number,csv_safe(inv.loan.student.full_name),en.grade if en else '',en.group if en else '',inv.book_count,csv_safe(books),inv.total,'Пардохтшуда' if inv.balance==0 else 'Пардохтнашуда',inv.created_at.date()])
    return response

@school_required()
@require_http_methods(['GET','POST'])
def sms_messages(request):
    from .notifications import requeue_sms
    if request.method=='POST':
        try:
            raw=request.POST.get('notification_id','')
            if not raw.isascii() or not raw.isdigit() or len(raw)>18:raise services.DomainError('Паём ёфт нашуд.')
            item=requeue_sms(user=request.user,school=request.school,notification_id=int(raw))
            messages.success(request,'SMS ба навбат гузошта шуд.' if item.status=='queued' else 'Маълумоти SMS нав шуд. Ҳолатро санҷед.')
            return redirect('sms_messages')
        except services.DomainError as exc:messages.error(request,str(exc))
    status=request.GET.get('status','');q=request.GET.get('q','').strip()
    qs=SmsNotification.objects.filter(invoice__school=request.school).select_related('invoice__loan__student').prefetch_related('parts').order_by('-id')
    if status in dict(SmsNotification._meta.get_field('status').choices):qs=qs.filter(status=status)
    if q:qs=qs.filter(Q(invoice__loan__student__full_name__icontains=q)|Q(destination__icontains=q))
    from django.conf import settings
    return page(request,'sms',active='sms',title='Паёмҳо ба волидайн',rows=paginate(request,qs),status=status,q=q,sms_backend=settings.SMS_BACKEND,sms_statuses=SmsNotification._meta.get_field('status').choices)

@school_required()
def account(request):
    from .models import Membership
    from django.conf import settings
    team=Membership.objects.filter(school=request.school).select_related('user').order_by('user__username') if request.member.role=='admin' else None
    return page(request,'account',active='account',title='Ҳисоби ман',team=team,sms_backend=settings.SMS_BACKEND)

@school_required('admin')
def audit_log(request):
    qs=AuditEvent.objects.filter(school=request.school).select_related('user').order_by('-id')
    return page(request,'audit',active='account',title='Таърихи амалҳо',rows=paginate(request,qs))
