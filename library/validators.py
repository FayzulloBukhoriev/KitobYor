import re
from django.core.exceptions import ValidationError

def normalize_parent_phone(value):
    phone=re.sub(r'[\s()\-]','',str(value or ''))
    if not phone:return ''
    if re.fullmatch(r'\d{9}',phone):phone='+992'+phone
    if re.fullmatch(r'992\d{9}',phone):phone='+'+phone
    if not re.fullmatch(r'\+992\d{9}',phone):
        raise ValidationError('Формат: +992XXXXXXXXX ё 9 рақами маҳаллӣ.')
    return phone
