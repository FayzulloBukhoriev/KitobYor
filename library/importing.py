"""Bounded, create-only import. Preview is stored server-side in Django session."""
import csv
import io
import hashlib
from zipfile import ZipFile, BadZipFile
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from xml.etree.ElementTree import ParseError
from django.db import transaction
from .forms import StudentForm
from .models import Student, ImportBatch
from . import services

HEADERS=['code','full_name','grade','group','address','language']
MAX_ROWS=500

def parse_upload(file=None,pasted=''):
    raw=file.read() if file else pasted.encode('utf-8')
    if len(raw)>2*1024*1024:raise services.DomainError('Ҳаҷм аз 2 MB зиёд аст.')
    if file and file.name.lower().endswith('.xlsx'):
        try:
            with ZipFile(io.BytesIO(raw)) as z:
                if len(z.infolist())>100 or sum(i.file_size for i in z.infolist())>10*1024*1024:
                    raise services.DomainError('Файли Excel аз ҳад калон аст.')
            wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=False)
            sheet=wb.active
            rows=[]
            if (sheet.max_row or 0)>MAX_ROWS+1:raise services.DomainError('Дар Excel то 500 сатр иҷозат аст; сатрҳои холии зиёдатиро тоза кунед.')
            for row in sheet.iter_rows(max_col=min(sheet.max_column or 7,7),values_only=True):
                if len(rows)>MAX_ROWS:raise services.DomainError('Дар як импорт то 500 хонанда иҷозат аст.')
                rows.append(list(row[:7]))
            wb.close()
        except (BadZipFile,ValueError,KeyError,OSError,InvalidFileException,ParseError) as exc:raise services.DomainError('Файли Excel хонда нашуд.') from exc
    else:
        if file and not file.name.lower().endswith('.csv'):raise services.DomainError('Формати CSV ё XLSX лозим аст.')
        try:text=raw.decode('utf-8-sig')
        except UnicodeDecodeError as exc:raise services.DomainError('CSV бояд UTF-8 бошад.') from exc
        first=text.splitlines()[0] if text.strip() else ''
        delimiter='\t' if '\t' in first else (';' if first.count(';')>first.count(',') else ',')
        rows=list(csv.reader(io.StringIO(text),delimiter=delimiter))
    if not rows:raise services.DomainError('Рӯйхат холӣ аст.')
    headers=[str(v or '').strip().lower() for v in rows[0]]
    if len(set(headers))!=len(headers) or set(headers)!=set(HEADERS):
        raise services.DomainError('Сутунҳо бояд code, full_name, grade, group, address, language бошанд. Намунаро боргирӣ кунед.')
    body=[r for r in rows[1:] if any(v is not None and str(v).strip() for v in r)]
    if not body or len(body)>MAX_ROWS:raise services.DomainError('Рӯйхат бояд 1–500 хонанда дошта бошад.')
    return [{h:str(r[i] if i<len(r) and r[i] is not None else '').strip() for i,h in enumerate(headers)} for r in body],hashlib.sha256(raw).hexdigest()

def validate_rows(rows,school):
    seen=set();existing=set(Student.objects.filter(school=school,code__in=[r.get('code','') for r in rows]).values_list('code',flat=True));result=[];valid=[]
    for number,row in enumerate(rows,2):
        form=StudentForm(row);ok=form.is_valid();errors=[]
        if not ok:errors=[f'{form.fields[k].label}: {", ".join(v)}' if k in form.fields else ', '.join(v) for k,v in form.errors.items()]
        code=row.get('code','')
        if code in seen or code in existing:errors.append('Рамз такрорӣ аст. Ин версия танҳо хонандаи нав илова мекунад.')
        seen.add(code)
        result.append({'number':number,'row':row,'errors':errors})
        if not errors:valid.append(form.cleaned_data)
    return result,valid

@transaction.atomic
def commit_import(*,user,school,rows,token,file_hash):
    services.authorize(user,school,['admin','librarian']);services.lock_school(school)
    old=ImportBatch.objects.filter(token=token).first()
    if old:
        if old.school_id!=school.pk or old.file_hash!=file_hash:raise services.DomainError('Импорт ба амали дигар тааллуқ дорад.','conflict',409)
        return 0
    checked,valid=validate_rows(rows,school)
    if len(valid)!=len(checked):raise services.DomainError('Маълумот тағйир ёфт ё такрор ёфт шуд. Пешнамоиши нав лозим аст.')
    for row in valid:services.add_student(user=user,school=school,**row)
    batch=ImportBatch.objects.create(school=school,token=token,file_hash=file_hash,state='committed',created_by=user)
    services.audit(school,user,'students.imported',batch.pk,str(len(valid)))
    return len(valid)
