from decimal import Decimal
from django import forms
from .models import Edition, Student

GRADES=[('', 'Ҳамаи синфҳо')]+[(n, f'Синфи {n}') for n in range(1,12)]
LANGUAGES=[('Тоҷикӣ','Тоҷикӣ'),('Русӣ','Русӣ'),('Ӯзбекӣ','Ӯзбекӣ')]

GROUPS=[(v,v) for v in 'ABCDE']

def normalize_group(value):
    return {'А':'A','Б':'B','В':'C','Г':'D','Д':'E','С':'C','Е':'E'}.get(str(value).strip().upper(),str(value).strip().upper())

class GroupField(forms.ChoiceField):
    def to_python(self,value):return normalize_group(value)

class StudentForm(forms.Form):
    full_name=forms.CharField(label='Ному насаби хонанда',max_length=200)
    grade=forms.TypedChoiceField(label='Синф',choices=GRADES[1:],coerce=int)
    group=GroupField(label='Гурӯҳ',choices=GROUPS,initial='A')
    language=forms.ChoiceField(label='Забони таҳсил',choices=LANGUAGES,required=False,initial='Тоҷикӣ')
    address=forms.CharField(label='Суроға',max_length=250)
    parent_name=forms.CharField(label='Номи падар ё модар',max_length=160,required=False)
    parent_phone=forms.CharField(label='Телефони падар ё модар',max_length=20,required=False,help_text='Барои SMS: +992 ва 9 рақам. Ҳоло танҳо пешнамоиши паём омода мешавад.')
    def clean_language(self):return self.cleaned_data.get('language') or 'Тоҷикӣ'
    def clean_parent_phone(self):
        from .validators import normalize_parent_phone
        return normalize_parent_phone(self.cleaned_data.get('parent_phone',''))

class CatalogForm(forms.Form):
    title=forms.CharField(label='Номи китоб',max_length=180)
    grade=forms.TypedChoiceField(label='Барои кадом синф',choices=GRADES[1:],coerce=int)
    year=forms.IntegerField(label='Соли нашр',min_value=1900,max_value=2100,initial=2025)
    quantity=forms.IntegerField(label='Шумораи нусхаҳо дар анбор',min_value=0,max_value=100000)
    fee=forms.DecimalField(label='Нархи иҷораи як китоб · сомонӣ',min_value=0,max_digits=10,decimal_places=2)
    def clean_title(self):return ' '.join(self.cleaned_data['title'].split())

class IntakeForm(forms.Form):
    quantity=forms.IntegerField(label='Шумораи нусхаҳои воридшуда',min_value=1,max_value=100000)
    note=forms.CharField(label='Асоси воридшавӣ',max_length=250)

class TariffForm(forms.Form):
    fee=forms.DecimalField(label='Нархи иҷора · сомонӣ',max_digits=10,decimal_places=2,min_value=0)
    note=forms.CharField(label='Асоси тариф ё имтиёз',max_length=250)
    approved=forms.BooleanField(label='Тариф тасдиқ шудааст',required=False)

class KitForm(forms.Form):
    name=forms.CharField(label='Номи маҷмӯа',max_length=120)
    grade=forms.TypedChoiceField(label='Синф',choices=GRADES[1:],coerce=int)
    language=forms.ChoiceField(label='Забони таҳсил',choices=LANGUAGES)
    def __init__(self,*args,school,**kwargs):
        super().__init__(*args,**kwargs)
        editions=Edition.objects.filter(book__school=school).select_related('book').order_by('book__grade','book__title','-year','id')
        for n in range(1,16):
            self.fields[f'edition_{n}']=forms.ModelChoiceField(label=f'Китоби {n}',queryset=editions,required=n<=5,empty_label='Интихоби китоб ва нашр')
            self.fields[f'alternatives_{n}']=forms.ModelMultipleChoiceField(label='Нашрҳои ивазшаванда',queryset=editions,required=False,widget=forms.SelectMultiple(attrs={'size':2}))
            for key in (f'edition_{n}',f'alternatives_{n}'):
                self.fields[key].label_from_instance=lambda ed:f'Синфи {ed.book.grade} · {ed.book.title} · {ed.year} · {ed.book.language} · {ed.code}'
    def clean(self):
        data=super().clean();items=[];seen=set()
        for n in range(1,16):
            ed=data.get(f'edition_{n}');alts=data.get(f'alternatives_{n}',[])
            if not ed:
                if alts:self.add_error(f'alternatives_{n}','Аввал нашри асосиро интихоб кунед.')
                continue
            if ed.book_id in seen:self.add_error(f'edition_{n}','Ин китоб такрор шудааст.')
            if (ed.book.grade,ed.book.language)!=(data.get('grade'),data.get('language')):self.add_error(f'edition_{n}','Синф ё забони китоб мувофиқ нест.')
            for alt in alts:
                if alt.book_id!=ed.book_id or alt.pk==ed.pk:self.add_error(f'alternatives_{n}','Танҳо нашри дигари ҳамон китоб иҷозат аст.')
            seen.add(ed.book_id);items.append({'preferred_id':ed.pk,'alternative_ids':[a.pk for a in alts]})
        data['items']=items
        return data

class PaymentForm(forms.Form):
    amount=forms.DecimalField(label='Маблағи пардохт · сомонӣ',max_digits=12,decimal_places=2,min_value=Decimal('0.01'))
    receipt=forms.CharField(label='Рақами ҳуҷҷати пардохт',max_length=120)
    note=forms.CharField(label='Асоси пардохт',max_length=250)
    token=forms.UUIDField(widget=forms.HiddenInput)

class ImportForm(forms.Form):
    file=forms.FileField(label='Файли CSV ё Excel (.xlsx)',required=False)
    pasted=forms.CharField(label='Ё рӯйхатро аз Excel гузоред',required=False,widget=forms.Textarea(attrs={'rows':7,'placeholder':'full_name\tgrade\tgroup\taddress\tparent_name\tparent_phone'}))
    def clean(self):
        data=super().clean()
        if bool(data.get('file'))==bool(data.get('pasted')):raise forms.ValidationError('Як роҳро интихоб кунед: файл ё гузоштани рӯйхат.')
        f=data.get('file')
        if f and f.size>2*1024*1024:self.add_error('file','Ҳаҷми файл бояд то 2 MB бошад.')
        return data
