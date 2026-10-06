# SMS тавассути GSM-модем · бе API-и провайдер

Дар 2.0 драйвери мустақими serial AT/PDU мавҷуд аст. Компютер ё сервер модеми SMS-capable ва SIM-корти фаъол дорад; худи SIM SMS-ро тавассути оператор мефиристад. Ҳисоби API ё HTTP gateway истифода намешавад. Баланс/хизматрасонии SMS, мувофиқати таҷҳизот ва шабака аз SIM/оператор вобастаанд.

## Танзими native

1. Модемро бо драйвераш пайваст кунед. Порти AT/SMS-ро ёбед: Windows, масалан COM3; Linux, масалан /dev/ttyUSB0. Инҳо намунаанд: рақами порти таҷҳизоти худро истифода кунед. PIN-и SIM ва хизматрасонии SMS бояд омода бошанд. check_sms_modem PIN-ро ворид намекунад.
2. Барои истифодаи воқеӣ PostgreSQL ва ҳисоби мактаби воқеӣ омода бошад. DEMO / config.demo_settings ҳеҷ паём намефиристад.
3. Дар .env:

```dotenv
SMS_BACKEND=gsm
SMS_MODEM_PORT=COM3
SMS_MODEM_BAUDRATE=115200
SMS_MODEM_TIMEOUT=45
```

Дар Linux ба ҷойи COM3 порти воқеии /dev/ttyUSB…-ро гузоред. Корбари worker бояд ба дастгоҳ ҳуқуқ дошта бошад (одатан гурӯҳи dialout). Як порт ба як worker тааллуқ дорад.
4. Бо Python-и .venv санҷед; ин фармон SMS намефиристад:

```bash
python manage.py check_sms_modem
```

Натиҷаи интизорӣ: `Modem, SIM and network ready. No SMS sent.` Агар дастгоҳ error диҳад, аввал порт/SIM/шабакаро ислоҳ кунед.
5. Worker:

```bash
python manage.py send_sms
```

Барои як паём ва баромадан:

```bash
python manage.py send_sms --once
```

Web process ва worker як база ва як конфигуратсияро истифода мебаранд. Барои Linux намунаи systemd дар deploy/kitobyor-sms.service аст. Роҳи /opt/kitobyor, корбари kitobyor ва /var/lib/kitobyor-ро ба насби худ мутобиқ кунед.

## Docker / Linux

Дар .env ҳам `SMS_BACKEND=gsm` гузоред, то веб паёмҳоро queued созад. `SMS_DEVICE` порти воқеии host, `SMS_DEVICE_GID` гурӯҳи рақамии соҳиби дастгоҳ мебошад. Онро бо `stat -c %g /dev/ttyUSB0` ёбед. Compose дастгоҳро ба /dev/ttyUSB0 дар worker мепайвандад. Веб-контейнер дастгоҳро намегирад.

```bash
docker compose --profile sms up -d --build
```

```bash
docker compose logs --tail 100 sms
```

Барои Docker Desktop/Windows USB passthrough кафолат дода нашудааст: роҳи native COM ё сервери Linux-и ба модем пайвастшударо истифода кунед.

## Ҳолатҳои дақиқ

| Ҳолат | Маъно |
|---|---|
| preview | Танҳо матн, фиристодан хомӯш |
| missing_phone | Телефони волидайн нест |
| queued | Барои worker омода |
| processing | Worker паёмро гирифтааст |
| retry | Пеш аз фиристодан хато; то 3 кӯшиш бо фосила |
| submitted | Ҳамаи қисмҳо бо +CMGS аз модем тасдиқ шуданд; delivery ба телефон тасдиқ нашудааст |
| uncertain | Қисм шояд қабул шудааст; худкор такрор намешавад |
| failed | Кӯшишҳо тамом шуданд ё маълумот нодуруст аст |

Матни тоҷикӣ бо UCS-2 код мешавад. SMS-и дароз ба қисмҳо бо reference-и 16-бит ҷудо мешавад, ҳадди 10 қисм. Ҳар қисм метавонад аз тарифи SIM ҳисоб шавад. Emoji берун аз UCS-2 рад мешавад; иҷора нигоҳ дошта шуда, SMS failed мешавад.

Транзаксияи иҷора танҳо outbox месозад. Worker берун аз транзаксия бо модем кор мекунад. Пеш аз ирсоли payload ҳолати submitting дар база сабт мешавад. Баъди қатъи worker қисмҳои тасдиқшуда дубора намераванд; қисмҳои шубҳанок uncertain мемонанд. OS lock як worker-и модемро таъмин мекунад; PostgreSQL claim сатри навбатро қулф мекунад.

## Барқароркунӣ

Барои preview/missing_phone/failed-и пурра нафиристодашуда, телефонро ислоҳ карда «Омода кардани SMS»-ро пахш кунед. Паёми queued/submitted/uncertain аз ин тугма дубора намеравад.

Барои uncertain ё фиристодани қисман, аввал модем/оператор ва қабулкунандаро санҷед. Оператори сервер бо номи маъмури ҳамин мактаб натиҷаи як қисмро қайд мекунад:

```bash
python manage.py resolve_sms --id 123 --part 2 --operator school-admin --outcome accepted --reference CHECKED-RECORD-123 --verified
```

Танҳо агар санҷиш нишон дод, ки қисм ирсол НАшудааст, `--outcome not-sent` истифода шавад. Қарори нодуруст метавонад SMS-ро такрор кунад. Амал аудит мешавад. `accepted` маънои тасдиқи шабака/модем дорад, на расиди хондани паём.

## Санҷиши қабул бо таҷҳизоти шумо

Бо мактаби воқеии санҷишӣ ва SIM-и худ: аввал як SMS-и кӯтоҳи тоҷикӣ, баъд паёми чандқисмӣ; қабулшавии телефон, матни Қ/Ҷ/Ҳ/Ӣ/Ӯ/Ғ, рақами пардохт ва маблағро муқоиса кунед. Қатъи модем, restart-и worker ва набудани балансро санҷед. То ин санҷишҳо дастгирии модеми мушаххас тасдиқшуда ҳисоб намешавад.

Манбаъҳои протокол: [ETSI TS 27.005](https://www.etsi.org/deliver/etsi_TS/127000_127099/127005/14.00.00_60/ts_127005v140000p.pdf), [pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).
