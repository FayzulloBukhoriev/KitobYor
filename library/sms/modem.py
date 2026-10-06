"""Bounded serial AT command transport (3GPP TS 27.005).

A +CMGS acknowledgement means network submission, NOT delivery to a handset.
Never retry an uncertain submission automatically.
"""
import os
import re
import time
import serial

class ModemError(Exception):pass
class SubmissionUncertain(ModemError):pass

class GsmModem:
    def __init__(self,port,baudrate=115200,timeout=45,serial_factory=serial.Serial):
        self.port=port;self.baudrate=baudrate;self.timeout=timeout;self.factory=serial_factory;self.device=None
    def __enter__(self):
        if not self.port:raise ModemError('Порти модем танзим нашудааст.')
        kwargs=dict(port=self.port,baudrate=self.baudrate,timeout=.2,write_timeout=5)
        if os.name=='posix':kwargs['exclusive']=True
        try:
            self.device=self.factory(**kwargs)
            self.device.reset_input_buffer()
            self.command('AT');self.command('ATE0')
            if '+CPIN: READY' not in self.command('AT+CPIN?'):raise ModemError('SIM омода нест; PIN ва SIM-кортро санҷед.')
            registered=False
            for cmd in ('AT+CREG?','AT+CEREG?'):
                try:response=self.command(cmd)
                except ModemError:continue
                if re.search(r'\+C(?:E)?REG:\s*\d+,\s*[15](?:\D|$)',response):registered=True;break
            if not registered:raise ModemError('Модем дар шабакаи мобилӣ сабт нашудааст.')
            self.command('AT+CMGF=0')
            return self
        except Exception as exc:
            self.__exit__(None,None,None)
            if isinstance(exc,ModemError):raise
            raise ModemError('Пайвастшавӣ ба модем муяссар нашуд; порт ва дастрасиро санҷед.') from exc
    def __exit__(self,*args):
        if self.device:self.device.close();self.device=None
    def read(self,prompt=False,timeout=None):
        until=time.monotonic()+(timeout or self.timeout);buffer=b''
        while time.monotonic()<until:
            buffer+=self.device.read(min(max(self.device.in_waiting,1),1024))
            if len(buffer)>8192:raise ModemError('Ҷавоби модем аз ҳад калон аст.')
            text=buffer.decode('ascii',errors='replace')
            if re.search(r'(?:^|\r?\n)(?:ERROR|\+CMS ERROR:.*|\+CME ERROR:.*)(?:\r?\n|$)',text):
                raise ModemError('Модем фармонро рад кард; SIM, баланс ва хизматрасонии SMS-ро санҷед.')
            if prompt and '>' in text:return text
            if not prompt and re.search(r'(?:^|\r?\n)OK\r?\n',text):return text
        raise ModemError('Вақти интизории ҷавоби модем гузашт.')
    def command(self,command):
        self.device.write((command+'\r').encode('ascii'))
        return self.read(timeout=8)
    def submit(self,part,before_submit):
        submitted=False
        try:
            self.device.write(f'AT+CMGS={part.tpdu_length}\r'.encode('ascii'))
            self.read(prompt=True,timeout=10)
            # Persist uncertainty boundary BEFORE any payload can reach the network.
            before_submit()
            submitted=True
            self.device.write(part.pdu.encode('ascii')+b'\x1a')
            response=self.read()
            match=re.search(r'\+CMGS:\s*(\d+)',response)
            if not match:raise SubmissionUncertain('Ҷавоби қабули SMS гирифта нашуд.')
            return match.group(1)
        except Exception as exc:
            if submitted:
                raise SubmissionUncertain('Натиҷаи фиристодан номаълум аст. Пеш аз такрор SIM ва қабулкунандаро санҷед.') from exc
            if self.device:
                try:self.device.write(b'\x1b')
                except serial.SerialException:pass
            if isinstance(exc,ModemError):raise
            raise ModemError('Пайвасти модем пеш аз фиристодан қатъ шуд.') from exc
