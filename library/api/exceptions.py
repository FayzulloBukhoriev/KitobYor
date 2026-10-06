from rest_framework.views import exception_handler as drf_handler
from rest_framework.response import Response
from library.services import DomainError
from django.core.exceptions import ValidationError

def exception_handler(exc,context):
    if isinstance(exc,DomainError):
        return Response({'code':exc.code,'detail':str(exc)},status=exc.status)
    if isinstance(exc,ValidationError):
        return Response({'code':'validation_error','detail':exc.message_dict if hasattr(exc,'message_dict') else exc.messages},status=400)
    return drf_handler(exc,context)
