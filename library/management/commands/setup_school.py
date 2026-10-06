from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from library.models import School, Membership

class Command(BaseCommand):
    help='Create a school and its administrator; password is entered privately.'
    def add_arguments(self,parser):
        parser.add_argument('--code',required=True)
        parser.add_argument('--name',required=True)
        parser.add_argument('--username',required=True)
        parser.add_argument('--year',default='2026-2027')
    def handle(self,*args,**opts):
        User=get_user_model()
        if School.objects.filter(code=opts['code']).exists() or User.objects.filter(username=opts['username']).exists():
            raise CommandError('School code or username already exists. Nothing changed.')
        password=getpass('Password: ')
        if password!=getpass('Repeat password: '):raise CommandError('Passwords do not match.')
        user=User(username=opts['username'])
        try:validate_password(password,user)
        except ValidationError as exc:raise CommandError('; '.join(exc.messages))
        with transaction.atomic():
            school=School(name=opts['name'],code=opts['code'],academic_year=opts['year']);school.full_clean();school.save()
            user.set_password(password);user.full_clean();user.save()
            Membership.objects.create(user=user,school=school,role='admin')
        self.stdout.write(self.style.SUCCESS('School administrator created. Sign in at /login/.'))
