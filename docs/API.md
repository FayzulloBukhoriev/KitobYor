# API v1

Base: `/api/v1/`. JSON. Login дар `/login/` бо form ва CSRF; session cookie-и браузер. Барои POST API header-и `X-CSRFToken` ва session cookie лозим. Register ва school_id дар payload нест.

| Method | Path | Вазифа |
|---|---|---|
| GET, POST | students/ | Ҷустуҷӯ `q`, филтр `grade`, эҷоди хонанда |
| GET, POST | editions/ | Нашр ва бақия; ҷустуҷӯ `q`; иловаи каталог |
| POST | editions/{id}/intake/ | quantity, note |
| POST | editions/{id}/tariff/ | fee, note, approved; admin/accountant |
| GET, POST | kits/ | Маҷмӯаҳо; 5–15 items |
| GET | issues/preview/?student_id=1&kit_id=1 | Нашрҳои пешниҳодшуда ва estimated_total |
| POST | issues/confirm/ | Додани интихобҳои тасдиқшуда |
| GET | invoices/ | Ҳисобҳо бо хонанда, китобҳо, total/paid/balance |
| GET | invoices/{id}/ | Як ҳисоб |
| POST | invoices/{id}/payments/ | Пардохти дастӣ; admin/accountant |
| POST | loans/{id}/returns/ | Баргардонӣ/осеб/гумшавӣ |

Рӯйхатҳо pagination доранд: `count`, `next`, `previous`, `results`; 50 сатр дар саҳифа.

## Эҷоди хонанда

```json
{"code":"S001","full_name":"Хонандаи намунавӣ","grade":5,"group":"А","address":"Суроғаи намунавӣ","language":"Тоҷикӣ"}
```

## Эҷоди нашр

```json
{"book_code":"B001","title":"Математика","grade":5,"language":"Тоҷикӣ","edition_code":"2024-1","year":2024,"publisher":"","isbn":""}
```

Book бо book_code-и мавҷуда танҳо вақте истифода мешавад, ки title/grade/language мувофиқ бошад. Бақияи нашри нав сифр аст; баъд intake ва тарифи тасдиқшуда лозим.

## Эҷоди маҷмӯа

```json
{"name":"Синфи 5","grade":5,"language":"Тоҷикӣ","items":[{"preferred_id":1,"alternative_ids":[2]},{"preferred_id":3},{"preferred_id":4},{"preferred_id":5},{"preferred_id":6}]}
```

ID-ҳо намунаанд; аз базаи воқеӣ гирифта шаванд.

## Тасдиқи қисман додан

```json
{"student_id":1,"kit_id":1,"choices":[{"kit_item_id":1,"edition_id":1}],"token":"ff82562a-e577-4868-9bac-398173ac4f39","expected_total":"2.00","allow_partial":true}
```

Маблағи 2.00 танҳо намунаи API аст, тарифи расмӣ нест. UUID-и нав барои ҳар амали нав; барои retry ҳамон UUID ва payload. expected_total аз пешнамоиш гирифта шавад. Ҷавоб Invoice бо lines ва reference.

## Пардохт ва баргардонӣ

```json
{"amount":"2.00","receipt":"DOC-001","note":"Асоси ҳуҷҷат","token":"f17b9b1e-2c6a-4e08-b290-7786065d1274"}
```

```json
{"lines":[{"line_id":1,"state":"returned"}]}
```

Ҳолатҳо: returned, damaged, lost. Иваз кардани ҳолати аллакай баста рад мешавад; такрори ҳамон баргардонӣ анборро дубора зиёд намекунад.

## Хатогиҳо

Domain errors: `{"code":"stock_changed","detail":"..."}`. 400 маълумоти нодуруст; 403 дастрасӣ/CSRF; 404 маълумоти мактаби дигар ё ID-и номавҷуд; 409 нарх/бақия/такрор. Хатогиҳои serializer бо номи майдон бармегарданд. Барои корбари невурудшуда SessionAuthentication метавонад 403 баргардонад.

## Барои frontend

Як origin барои UI ва API интихоб шудааст: CORS ва JWT ҳоло лозим нестанд. Пардохт ё дода шудани китобро аз рӯи танҳо UI-state ҳисоб накунед; натиҷаи серверро қабул кунед. Агар ҷавоби confirm гум шавад, payload ва token-ро бетағйир retry кунед. 409 → пешнамоиши нав → тасдиқи корбар → token-и нав.

UI-и корӣ дар /students/, /inventory/, /kits/, /issue/, /invoices/, /returns/ ва /reports/ аст. API-и JSON нигоҳ дошта шудааст; корбари оддӣ аз templates истифода мекунад. Импорт ҳоло тавассути UI аст.
