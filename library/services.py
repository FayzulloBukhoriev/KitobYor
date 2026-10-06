"""Business commands. Atomic stock, loans, invoices and audit events."""
import hashlib
import json
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import (School,Membership,Student,Enrollment,Book,Edition,Stock,Tariff,Kit,KitItem,Loan,LoanLine,Invoice,Payment,StockMovement,AuditEvent)

class DomainError(Exception):
    def __init__(self,message,code='invalid',status=400):
        super().__init__(message)
        self.code,self.status=code,status

def fingerprint(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()

def authorize(user,school,roles):
    if not Membership.objects.filter(user=user,school=school,role__in=roles).exists():
        raise DomainError('Барои ин амал ваколат надоред.','forbidden',403)

def lock_school(school):
    # Initial coarse write lock: one brief command per school at a time.
    # Different schools remain independent. Must not perform network I/O in this lock.
    return School.objects.select_for_update().get(pk=school.pk)

def audit(school,user,action,obj,detail=''):
    AuditEvent.objects.create(school=school,user=user,action=action,object_id=str(obj),detail=detail)

def find(qs,pk):
    try: return qs.get(pk=pk)
    except qs.model.DoesNotExist: raise DomainError('Маълумот ёфт нашуд.','not_found',404)

def enrollment(student,school):
    try: return student.enrollments.get(academic_year=school.academic_year)
    except Enrollment.DoesNotExist: raise DomainError('Хонанда дар соли ҷорӣ синфи тасдиқшуда надорад.')

def eligible(item,school):
    choices=[item.preferred,*item.alternatives.all()]
    for ed in choices:
        if ed.book.school_id!=school.pk or ed.book_id!=item.preferred.book_id:
            raise DomainError('Нашри маҷмӯа ба китоб ё мактаб мувофиқ нест.')
    return choices

def kit_for_student(school,student,kit_id):
    if not student.active: raise DomainError('Хонанда ғайрифаъол аст.')
    kit=find(Kit.objects.filter(school=school),kit_id)
    en=enrollment(student,school)
    if (kit.grade,kit.language,kit.academic_year)!=(en.grade,en.language,school.academic_year):
        raise DomainError('Маҷмӯа ба синф, забон ё соли таҳсили хонанда мувофиқ нест.')
    return kit

def preview_issue(school,student_id,kit_id):
    student=find(Student.objects.filter(school=school),student_id)
    kit=kit_for_student(school,student,kit_id)
    held=set(LoanLine.objects.filter(student=student,state='issued').values_list('kit_item_id',flat=True))
    rows=[]
    for item in kit.items.select_related('preferred__book').prefetch_related('alternatives__book'):
        choices=[]
        for ed in eligible(item,school):
            tariff=ed.tariffs.filter(academic_year=school.academic_year,approved=True).first()
            stock=Stock.objects.filter(edition=ed).first()
            choices.append({'edition_id':ed.pk,'year':ed.year,'available':stock.available if stock else 0,'fee':str(tariff.fee) if tariff else None,'approved':bool(tariff)})
        choice=next((c for c in choices if c['available']>0 and c['approved']),None)
        rows.append({'kit_item_id':item.pk,'title':item.label,'already_held':item.pk in held,'suggested':None if item.pk in held else choice,'choices':choices})
    total=sum((Decimal(r['suggested']['fee']) for r in rows if r['suggested']),Decimal('0.00'))
    return {'student_id':student.pk,'kit_id':kit.pk,'academic_year':school.academic_year,'items':rows,'estimated_total':str(total)}

@transaction.atomic
def add_student(*,user,school,code,full_name,address,grade,group,language='Тоҷикӣ'):
    authorize(user,school,['admin','librarian'])
    lock_school(school)
    if Student.objects.filter(school=school,code=code).exists(): raise DomainError('Рамзи хонанда такрорӣ аст.','conflict',409)
    s=Student(school=school,code=code,full_name=full_name,address=address)
    s.full_clean();s.save()
    en=Enrollment(student=s,academic_year=school.academic_year,grade=grade,group=group,language=language)
    en.full_clean();en.save()
    audit(school,user,'student.created',s.pk)
    return s

@transaction.atomic
def intake(*,user,school,edition_id,quantity,note):
    authorize(user,school,['admin','librarian'])
    lock_school(school)
    if quantity<=0 or not note.strip(): raise DomainError('Шумораи мусбат ва асоси воридшавӣ лозим аст.')
    ed=find(Edition.objects.filter(book__school=school),edition_id)
    stock,_=Stock.objects.get_or_create(edition=ed)
    Stock.objects.filter(pk=stock.pk).update(available=F('available')+quantity)
    StockMovement.objects.create(edition=ed,delta_available=quantity,kind='intake',note=note,created_by=user)
    audit(school,user,'stock.intake',ed.pk,str(quantity))
    stock.refresh_from_db();return stock

@transaction.atomic
def create_catalog(*,user,school,book_code,title,grade,language,edition_code,year,publisher='',isbn=''):
    authorize(user,school,['admin','librarian'])
    lock_school(school)
    book=Book.objects.filter(school=school,code=book_code).first()
    if book and (book.title,book.grade,book.language)!=(title,grade,language):
        raise DomainError('Рамзи китоб ба маълумоти дигар тааллуқ дорад.','conflict',409)
    if not book:
        book=Book(school=school,code=book_code,title=title,grade=grade,language=language)
        book.full_clean();book.save()
    if Edition.objects.filter(book=book,code=edition_code).exists(): raise DomainError('Нашр аллакай ҳаст.','conflict',409)
    ed=Edition(book=book,code=edition_code,year=year,publisher=publisher,isbn=isbn)
    ed.full_clean();ed.save();Stock.objects.create(edition=ed)
    audit(school,user,'edition.created',ed.pk)
    return ed

@transaction.atomic
def set_tariff(*,user,school,edition_id,fee,note,approved):
    authorize(user,school,['admin','accountant'])
    lock_school(school)
    ed=find(Edition.objects.filter(book__school=school),edition_id)
    if not note.strip(): raise DomainError('Асоси тариф ё озодкунӣ лозим аст.')
    tariff,_=Tariff.objects.get_or_create(edition=ed,academic_year=school.academic_year,defaults={'fee':fee})
    tariff.fee,tariff.note,tariff.approved=fee,note,approved
    tariff.full_clean();tariff.save()
    audit(school,user,'tariff.changed',tariff.pk,f'{fee}; approved={approved}')
    return tariff

@transaction.atomic
def create_kit(*,user,school,name,grade,language,items):
    authorize(user,school,['admin','librarian'])
    lock_school(school)
    if not 5<=len(items)<=15: raise DomainError('Маҷмӯа бояд 5–15 мавқеъ дошта бошад.')
    if Kit.objects.filter(school=school,grade=grade,language=language,academic_year=school.academic_year).exists():
        raise DomainError('Маҷмӯаи ин синф аллакай ҳаст.','conflict',409)
    kit=Kit(school=school,name=name,grade=grade,language=language,academic_year=school.academic_year)
    kit.full_clean();kit.save();seen=set()
    for pos,entry in enumerate(items):
        ed=find(Edition.objects.filter(book__school=school),entry['preferred_id'])
        if ed.book_id in seen or (ed.book.grade,ed.book.language)!=(grade,language):
            raise DomainError('Китоби такрорӣ ё ба синф/забон номувофиқ.')
        seen.add(ed.book_id)
        item=KitItem.objects.create(kit=kit,label=ed.book.title,preferred=ed,position=pos)
        for alternative_id in entry.get('alternative_ids',[]):
            alt=find(Edition.objects.filter(book__school=school),alternative_id)
            if alt.book_id!=ed.book_id or alt.pk==ed.pk: raise DomainError('Алтернатива ба ҳамин китоб мувофиқ нест.')
            item.alternatives.add(alt)
    audit(school,user,'kit.created',kit.pk)
    return kit

@transaction.atomic
def confirm_issue(*,user,school,student_id,kit_id,choices,token,expected_total,allow_partial=False):
    authorize(user,school,['admin','librarian'])
    school=lock_school(school)
    payload={'student_id':student_id,'kit_id':kit_id,'choices':sorted(choices,key=lambda c:c['kit_item_id']),'expected_total':str(expected_total),'allow_partial':allow_partial}
    sig=fingerprint(payload)
    previous=Loan.objects.filter(token=token).first()
    if previous:
        if previous.school_id!=school.pk or previous.request_hash!=sig:
            raise DomainError('Калиди такрор ба амали дигар тааллуқ дорад.','idempotency_conflict',409)
        return previous.invoice
    student=find(Student.objects.filter(school=school),student_id)
    # Serialize loan writes for this school, then lock concrete stock rows in ascending id.
    kit=kit_for_student(school,student,kit_id)
    item_map={i.pk:i for i in kit.items.select_related('preferred__book').prefetch_related('alternatives__book')}
    if not choices: raise DomainError('Ҳадди ақал як китоб интихоб кунед.')
    selected_ids=[c['kit_item_id'] for c in choices]
    edition_ids=[c['edition_id'] for c in choices]
    if len(set(selected_ids))!=len(selected_ids) or len(set(edition_ids))!=len(edition_ids):
        raise DomainError('Китоб ё мавқеи такрорӣ интихоб шудааст.')
    held=set(LoanLine.objects.filter(student=student,state='issued').values_list('kit_item_id',flat=True))
    if set(selected_ids)&held: raise DomainError('Хонанда ин китобро аллакай гирифтааст.','already_held',409)
    if set(selected_ids)!=set(item_map)-held and not allow_partial:
        raise DomainError('Додани қисмиро равшан тасдиқ кунед.','partial_required',409)
    stock_map={s.edition_id:s for s in Stock.objects.select_for_update().filter(edition_id__in=edition_ids,edition__book__school=school).order_by('pk')}
    selected=[]
    for choice in choices:
        item=item_map.get(choice['kit_item_id'])
        if item is None: raise DomainError('Мавқеъ ба маҷмӯа тааллуқ надорад.')
        ed=next((e for e in eligible(item,school) if e.pk==choice['edition_id']),None)
        if ed is None: raise DomainError('Нашри ивазшаванда иҷозат надорад.')
        stock=stock_map.get(ed.pk)
        if not stock or stock.available<1: raise DomainError('Бақияи анбор тағйир ёфт.','stock_changed',409)
        if LoanLine.objects.filter(student=student,edition=ed,state='issued').exists():
            raise DomainError('Хонанда ин нашрро аллакай гирифтааст.','already_held',409)
        tariff=ed.tariffs.filter(academic_year=school.academic_year,approved=True).first()
        if not tariff: raise DomainError('Тарифи тасдиқшуда нест.','tariff_missing',409)
        selected.append((item,ed,tariff))
    total=sum((t.fee for _,_,t in selected),Decimal('0.00'))
    if total!=expected_total: raise DomainError('Нарх тағйир ёфт. Маблағи навро санҷед.','price_changed',409)
    loan=Loan.objects.create(school=school,student=student,kit=kit,academic_year=school.academic_year,token=token,request_hash=sig,created_by=user)
    for item,ed,tariff in selected:
        changed=Stock.objects.filter(pk=stock_map[ed.pk].pk,available__gte=1).update(available=F('available')-1)
        if changed!=1: raise DomainError('Китоб дигар дастрас нест.','stock_changed',409)
        LoanLine.objects.create(loan=loan,student=student,edition=ed,kit_item=item,tariff=tariff,title_snapshot=ed.book.title,year_snapshot=ed.year,fee_snapshot=tariff.fee)
        StockMovement.objects.create(edition=ed,delta_available=-1,kind='issue',object_id=str(loan.pk),note='Додани китоб',created_by=user)
    invoice=Invoice.objects.create(school=school,loan=loan,total=total)
    audit(school,user,'loan.issued',loan.pk)
    return invoice

@transaction.atomic
def record_payment(*,user,school,invoice_id,amount,receipt,note,token):
    authorize(user,school,['admin','accountant'])
    lock_school(school)
    sig=fingerprint({'invoice_id':invoice_id,'amount':str(amount),'receipt':receipt,'note':note})
    old=Payment.objects.filter(token=token).first()
    if old:
        if old.school_id!=school.pk or old.request_hash!=sig: raise DomainError('Калиди такрорӣ ба амали дигар тааллуқ дорад.','idempotency_conflict',409)
        return old
    inv=find(Invoice.objects.select_for_update().filter(school=school),invoice_id)
    if not amount.is_finite() or amount<=0 or amount>inv.balance: raise DomainError('Маблағ бояд мусбат ва аз бақия зиёд набошад.')
    if not receipt.strip() or not note.strip(): raise DomainError('Рақами ҳуҷҷат ва асоси пардохт лозим аст.')
    if Payment.objects.filter(school=school,receipt=receipt).exists(): raise DomainError('Ҳуҷҷати пардохт аллакай сабт шудааст.','receipt_duplicate',409)
    pay=Payment.objects.create(school=school,invoice=inv,amount=amount,receipt=receipt,note=note,token=token,request_hash=sig,created_by=user)
    inv.paid+=amount;inv.save(update_fields=['paid'])
    audit(school,user,'payment.recorded',pay.pk)
    return pay

@transaction.atomic
def close_lines(*,user,school,loan_id,lines):
    authorize(user,school,['admin','librarian'])
    lock_school(school)
    loan=find(Loan.objects.filter(school=school),loan_id)
    if not lines: raise DomainError('Китоб интихоб нашудааст.')
    if len({r['line_id'] for r in lines})!=len(lines): raise DomainError('Сатри такрорӣ.')
    closed=[]
    for entry in lines:
        state=entry['state']
        if state not in ['returned','damaged','lost']: raise DomainError('Ҳолати китоб нодуруст аст.')
        line=find(LoanLine.objects.select_for_update().filter(loan=loan),entry['line_id'])
        if line.state!='issued':
            if line.state!=state: raise DomainError('Китоб бо ҳолати дигар баста шудааст.','conflict',409)
            continue # safe repeated return, no duplicate stock movement
        if state!='lost':
            field='available' if state=='returned' else 'damaged'
            if Stock.objects.filter(edition=line.edition).update(**{field:F(field)+1})!=1:
                raise DomainError('Бақияи нашр ёфт нашуд.')
        line.state=state;line.closed_at=timezone.now();line.save(update_fields=['state','closed_at'])
        StockMovement.objects.create(edition=line.edition,delta_available=int(state=='returned'),delta_damaged=int(state=='damaged'),kind=state,object_id=str(line.pk),note='Анҷоми иҷораи китоб',created_by=user)
        closed.append(line.pk)
    audit(school,user,'loan.closed',loan.pk,','.join(map(str,closed)))
    # Invoice balance never changes on a return. Refunds are a separate future workflow.
    return loan

@transaction.atomic
def update_student(*,user,school,student_id,code,full_name,address,grade,group,language):
    authorize(user,school,['admin','librarian']);lock_school(school)
    student=find(Student.objects.filter(school=school),student_id)
    student.code,student.full_name,student.address=code,full_name,address
    student.full_clean();student.save()
    en=find(Enrollment.objects.filter(student=student,academic_year=school.academic_year),enrollment(student,school).pk)
    en.grade,en.group,en.language=grade,group,language;en.full_clean();en.save()
    audit(school,user,'student.updated',student.pk)
    return student
