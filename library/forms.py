from decimal import Decimal
from django import forms
from .models import Edition, Student

GRADES=[('', 'Ҳамаи синфҳо')]+[(n, f'Синфи {n}') for n in range(1,12)]
LANGUAGES=[('Тоҷикӣ','Тоҷикӣ'),('Русӣ','Русӣ'),('Ӯзбекӣ','Ӯзбекӣ')]

class StudentForm(forms.Form):
    code=forms.CharField(label='Рамзи хонанда',max_length=40)
    full_name=forms.CharField(label='Ному насаб',max_length=200)
    grade=forms.TypedChoiceField(label='Синф',choices=GRADES[1:],coerce=int)
    group=forms.CharField(label='Гурӯҳ',max_length=8,initial='А')
    language=forms.ChoiceField(label='Забони таҳсил',choices=LANGUAGES)
    address=forms.CharField(label='Суроға',max_length=250)

class CatalogForm(forms.Form):
    book_code=forms.CharField(label='Рамзи китоб',max_length=60,help_text='Барои нашри нави ҳамон китоб рамзи мавҷударо истифода баред.')
    title=forms.CharField(label='Номи китоб',max_length=180)
    grade=forms.TypedChoiceField(label='Синф',choices=GRADES[1:],coerce=int)
    language=forms.ChoiceField(label='Забон',choices=LANGUAGES)
    edition_code=forms.CharField(label='Рамзи нашр',max_length=60)
    year=forms.IntegerField(label='Соли нашр',min_value=1900,max_value=2100,initial=2024)
    publisher=forms.CharField(label='Нашриёт',max_length=120,required=False)
    isbn=forms.CharField(label='ISBN',max_length=20,required=False)

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
    pasted=forms.CharField(label='Ё рӯйхатро аз Excel гузоред',required=False,widget=forms.Textarea(attrs={'rows':7,'placeholder':'code\tfull_name\tgrade\tgroup\taddress\tlanguage'}))
    def clean(self):
        data=super().clean()
        if bool(data.get('file'))==bool(data.get('pasted')):raise forms.ValidationError('Як роҳро интихоб кунед: файл ё гузоштани рӯйхат.')
        f=data.get('file')
        if f and f.size>2*1024*1024:self.add_error('file','Ҳаҷми файл бояд то 2 MB бошад.')
        return data
