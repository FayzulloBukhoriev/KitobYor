from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase,SimpleTestCase,override_settings
from django.utils import timezone
from .tests import fixture
from .models import SmsNotification,SmsPart,Membership
from . import services
from .notifications import requeue_sms
from .sms.pdu import encode_message
from .sms.modem import GsmModem,ModemError,SubmissionUncertain
from .sms.worker import process_one,recover_stale

class PduTests(SimpleTestCase):
    def test_tajik_unicode_destination_and_length(self):
        body='Китобҳо: 12.50 сомонӣ.';part=encode_message('+992900000001',body,256)[0]
        raw=bytes.fromhex(part.hex)
        self.assertEqual(raw[:5],bytes([0,1,0,12,0x91]));self.assertEqual(raw[5:11].hex(),'999200000010')
        self.assertEqual(raw[11:13],bytes([0,8]));self.assertEqual(raw[14:].decode('utf-16-be'),body)
        self.assertEqual(part.length,len(raw)-1);self.assertEqual(raw[13],len(raw[14:]))
    def test_multipart_round_trip_and_distinct_sequence(self):
        body='Ҳар як китоб дониш аст. '*20;parts=encode_message('+992900000001',body,0xABCD)
        self.assertGreater(len(parts),1);decoded=''
        for part in parts:
            raw=bytes.fromhex(part.hex);payload=raw[14:]
            self.assertEqual(raw[1],0x41);self.assertLessEqual(len(payload),140)
            self.assertEqual(payload[:7],bytes([6,8,4,0xAB,0xCD,len(parts),part.sequence]))
            decoded+=payload[7:].decode('utf-16-be')
        self.assertEqual(decoded,body)
    def test_limits_and_non_ucs2(self):
        with self.assertRaises(ValueError):encode_message('+992900000001','x'*1000,1)
        with self.assertRaises(ValueError):encode_message('+992900000001','😀',1)
    def test_single_part_boundary(self):
        self.assertEqual(len(encode_message('+992900000001','А'*70,1)),1)
        self.assertEqual(len(encode_message('+992900000001','А'*71,1)),2)

class ScriptedSerial:
    def __init__(self,**kwargs):self.buffer=b'';self.commands=[];self.closed=False
    @property
    def in_waiting(self):return len(self.buffer)
    def reset_input_buffer(self):self.buffer=b''
    def close(self):self.closed=True
    def write(self,data):
        self.commands.append(data)
        if data==b'AT+CPIN?\r':self.buffer=b'\r\n+CPIN: READY\r\nOK\r\n'
        elif data==b'AT+CREG?\r':self.buffer=b'\r\n+CREG: 0,1\r\nOK\r\n'
        elif data.startswith(b'AT+CMGS='):self.buffer=b'\r\n> '
        elif data.endswith(b'\x1a'):self.buffer=b'\r\n+CMGS: 42\r\nOK\r\n'
        else:self.buffer=b'\r\nOK\r\n'
        return len(data)
    def read(self,n):data=self.buffer[:n];self.buffer=self.buffer[n:];return data

class ModemProtocolTests(SimpleTestCase):
    def test_real_transport_command_order_with_simulated_serial(self):
        serial=ScriptedSerial();flags=[]
        encoded=encode_message('+992900000001','Салом',1)[0]
        with GsmModem('TEST',serial_factory=lambda **kw:serial) as modem:
            part=SimpleNamespace(pdu=encoded.hex,tpdu_length=encoded.length)
            self.assertEqual(modem.submit(part,lambda:flags.append(len(serial.commands))),'42')
        self.assertTrue(serial.closed);self.assertEqual(len(flags),1)
        self.assertTrue(serial.commands[-2].startswith(b'AT+CMGS='))
        self.assertEqual(serial.commands[-1],encoded.hex.encode()+b'\x1a')
        self.assertEqual(flags[0],len(serial.commands)-1)
    def test_timeout_after_payload_is_uncertain(self):
        modem=GsmModem('TEST');modem.device=ScriptedSerial()
        with patch.object(modem,'read',side_effect=['>',ModemError('timeout')]):
            with self.assertRaises(SubmissionUncertain):modem.submit(SimpleNamespace(pdu='00',tpdu_length=1),lambda:None)

class AcceptedModem:
    calls=[]
    def __init__(self,*args):pass
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def submit(self,part,before_submit):before_submit();self.calls.append(part.pk);return str(part.sequence)
class OfflineModem(AcceptedModem):
    def __enter__(self):raise ModemError('Модем дастрас нест.')
class UncertainModem(AcceptedModem):
    def submit(self,part,before_submit):before_submit();raise SubmissionUncertain('Ҷавоб гирифта нашуд.')

@override_settings(SMS_BACKEND='gsm',DEMO_MODE=False,SMS_MODEM_PORT='TEST')
class SmsWorkerTests(TestCase):
    def setUp(self):
        fixture(self);self.student.parent_phone='+992900000001';self.student.save();AcceptedModem.calls=[]
    def invoice(self):
        return services.confirm_catalog_issue(user=self.user,school=self.school,student_id=self.student.pk,edition_ids=[self.items[0].preferred_id],token=uuid4(),expected_total=Decimal('2.00'))
    def test_issue_only_queues_then_worker_submits_once(self):
        sms=self.invoice().sms_notification
        self.assertEqual(sms.status,'queued');self.assertTrue(sms.parts.exists());self.assertFalse(AcceptedModem.calls)
        result=process_one(AcceptedModem);self.assertEqual(result.status,'submitted')
        self.assertIsNotNone(result.sent_at);self.assertEqual(len(AcceptedModem.calls),sms.parts.count())
        self.assertIsNone(process_one(AcceptedModem))
    def test_no_modem_retries_bounded_and_never_sent(self):
        sms=self.invoice().sms_notification
        for n in range(3):
            SmsNotification.objects.filter(pk=sms.pk).update(next_attempt_at=timezone.now())
            result=process_one(OfflineModem)
            self.assertEqual(result.attempts,n+1);self.assertIsNone(result.sent_at)
        self.assertEqual(result.status,'failed');self.assertIsNone(process_one(OfflineModem))
    def test_unknown_result_is_not_resent(self):
        sms=self.invoice().sms_notification;result=process_one(UncertainModem)
        self.assertEqual(result.status,'uncertain');self.assertEqual(sms.parts.first().status,'uncertain')
        self.assertIsNone(process_one(AcceptedModem))
        with self.assertRaises(services.DomainError):requeue_sms(user=self.user,school=self.school,notification_id=sms.pk)
    def test_stale_worker_marks_in_flight_unknown(self):
        sms=self.invoice().sms_notification
        SmsNotification.objects.filter(pk=sms.pk).update(status='processing',locked_at=timezone.now()-timedelta(minutes=20))
        sms.parts.filter(sequence=1).update(status='submitting')
        recover_stale();sms.refresh_from_db();self.assertEqual(sms.status,'uncertain')
        self.assertIsNone(process_one(AcceptedModem))
    def test_demo_never_queues_or_sends(self):
        self.school.code='DEMO';self.school.save();sms=self.invoice().sms_notification
        self.assertEqual(sms.status,'preview');self.assertIsNone(process_one(AcceptedModem))
    def test_missing_phone_then_prepare_uses_updated_phone(self):
        self.student.parent_phone='';self.student.save();sms=self.invoice().sms_notification
        self.assertEqual(sms.status,'missing_phone')
        self.student.parent_phone='+992900000001';self.student.save()
        sms=requeue_sms(user=self.user,school=self.school,notification_id=sms.pk)
        self.assertEqual(sms.status,'queued');self.assertTrue(sms.parts.exists())
    def test_accountant_cannot_queue_sms(self):
        sms=self.invoice().sms_notification;Membership.objects.filter(user=self.user).update(role='accountant')
        with self.assertRaises(services.DomainError):requeue_sms(user=self.user,school=self.school,notification_id=sms.pk)
    def test_partial_success_resumes_only_unsent_parts(self):
        sms=self.invoice().sms_notification
        if sms.parts.count()<2:self.fail('Fixture requires multipart SMS')
        first=sms.parts.first();first.status='submitted';first.reference='41';first.save()
        process_one(AcceptedModem);self.assertNotIn(first.pk,AcceptedModem.calls)
    def test_worker_restart_recovers_recent_claim_without_resending_accepted_parts(self):
        sms=self.invoice().sms_notification
        SmsNotification.objects.filter(pk=sms.pk).update(status='processing',locked_at=timezone.now())
        sms.parts.all().update(status='submitted',reference='7',submitted_at=timezone.now())
        recover_stale();sms.refresh_from_db();self.assertEqual(sms.status,'submitted')
        self.assertIsNone(process_one(AcceptedModem))
    def test_preview_rows_never_sent_until_explicitly_queued(self):
        sms=self.invoice().sms_notification;SmsNotification.objects.filter(pk=sms.pk).update(status='preview')
        self.assertIsNone(process_one(AcceptedModem))
