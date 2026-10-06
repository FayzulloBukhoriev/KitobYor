from django import template
register=template.Library()
@register.filter
def current_enrollment(student,year):return next((e for e in student.enrollments.all() if e.academic_year==year),None)
@register.filter
def money(value):return f'{value:.2f}' if value is not None else '0.00'
