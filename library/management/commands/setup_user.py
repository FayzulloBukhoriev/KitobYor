from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand,CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from library.models import School,Membership

class Command(BaseCommand):
    help='Create a staff account for an existing school (private password prompt).'
    def add_arguments(self,p):
        p.add_argument('--school',required=True);p.add_argument('--username',required=True)
        p.add_argument('--role',choices=[r[0] for r in Membership.ROLES],required=True)
    def handle(self,*args,**opts):
        try:school=School.objects.get(code=opts['school'])
        except School.DoesNotExist:raise CommandError('School not found.')
        User=get_user_model()
        if User.objects.filter(username=opts['username']).exists():raise CommandError('Username already exists.')
        password=getpass('Password: ')
        if password!=getpass('Repeat password: '):raise CommandError('Passwords do not match.')
        user=User(username=opts['username'])
        try:
            validate_password(password,user)
            with transaction.atomic():
                user.set_password(password);user.full_clean();user.save()
                Membership.objects.create(school=school,user=user,role=opts['role'])
        except ValidationError as exc:raise CommandError('; '.join(exc.messages))
        self.stdout.write(self.style.SUCCESS('School account created.'))
