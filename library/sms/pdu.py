"""3GPP SMS-SUBMIT / UCS-2 with 16-bit concatenation references."""
from dataclasses import dataclass
from library.validators import normalize_parent_phone

@dataclass(frozen=True)
class EncodedPart:
    sequence: int
    hex: str
    length: int

def encode_message(destination, body, reference, max_parts=10):
    phone=normalize_parent_phone(destination)
    if not phone or not body.strip():raise ValueError('Телефон ё матни SMS холӣ аст.')
    if any(ord(c)>0xffff or 0xd800<=ord(c)<=0xdfff for c in body):
        raise ValueError('SMS танҳо ҳарфҳои UCS-2 мегирад; emoji-ро аз ном хориҷ кунед.')
    data=body.encode('utf-16-be')
    # 140 octets single part; multipart has a seven-octet 16-bit UDH.
    chunks=[data] if len(data)<=140 else [data[n:n+132] for n in range(0,len(data),132)]
    if len(chunks)>max_parts:raise ValueError('Матни SMS аз ҳад дароз аст.')
    digits=phone[1:];padded=digits+('F' if len(digits)%2 else '')
    address=bytes.fromhex(''.join(padded[i+1]+padded[i] for i in range(0,len(padded),2)))
    result=[]
    for n,chunk in enumerate(chunks,1):
        udh=bytes([6,8,4,(reference>>8)&255,reference&255,len(chunks),n]) if len(chunks)>1 else b''
        payload=udh+chunk
        tpdu=bytes([0x41 if udh else 0x01,0,len(digits),0x91])+address+bytes([0,8,len(payload)])+payload
        result.append(EncodedPart(n,(b'\x00'+tpdu).hex().upper(),len(tpdu)))
    return result
