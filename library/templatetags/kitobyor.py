from django import template
register=template.Library()
@register.filter
def current_enrollment(student,year):return next((e for e in student.enrollments.all() if e.academic_year==year),None)
@register.filter
def money(value):return f'{value:.2f}' if value is not None else '0.00'


@register.filter
def sms_tone(status):
    return {'submitted':'green','sent':'green','preview':'blue','queued':'blue','processing':'blue','retry':'amber','missing_phone':'amber','uncertain':'danger','failed':'danger'}.get(status,'blue')

@register.simple_tag
def icon(name):
    from django.utils.safestring import mark_safe
    paths={
      'book':'<path d="M12 5v15M12 5C8 2 4 3 2 4v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-2-1-6-2-10 1Z"/>',
      'dashboard':'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
      'users':'<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 4v2"/>',
      'inventory':'<path d="M4 4h16v16H4ZM4 10h16M9 4v6M15 10v10"/>',
      'issue':'<path d="M5 12h14m-6-6 6 6-6 6M3 5V3h4M3 19v2h4"/>',
      'invoice':'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2ZM9 7h6M9 11h6M9 15h3"/>',
      'chart':'<path d="M3 3v18h18M7 16v-5M12 16V7M17 16V4"/>',
      'sms':'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3 6 9 7 9-7"/>',
      'settings':'<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>',
      'logout':'<path d="M10 4H4v16h6M9 12h12m-4-4 4 4-4 4"/>',
      'search':'<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
      'plus':'<path d="M12 5v14M5 12h14"/>',
      'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
      'shield':'<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6ZM8 12l3 3 5-6"/>',
      'calendar':'<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 2v6M17 2v6M3 11h18"/>',
      'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
      'check':'<path d="m5 12 4 4L19 6"/>',
      'download':'<path d="M12 3v12m-5-5 5 5 5-5M3 15v6h18v-6"/>',
      'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    }
    return mark_safe('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths.get(name,paths['book'])+'</svg>')
