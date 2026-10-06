# REST API · KitobYor 2.0

Prefix /api/v1/. SessionAuthentication + CSRF; ҳамаи маълумот аз мактаби login. Pagination барои list. POST role-ро санҷида, query-ро бо мактаб маҳдуд мекунад. Ошибка: 400 validation, 403 permission/CSRF, 404 scoped ID, 409 stock/price/idempotency conflict.

| Route | Амал |
|---|---|
| GET/POST students/ | Хонандагон; code ихтиёрӣ барои compatibility, UI худкор |
| GET/POST catalog/ | Анбор; title, grade, year, quantity, fee |
| POST catalog/{edition_id}/ | Иваз кардани анбор; expected_revision ҳатмӣ, quantity бақияи дастрас мешавад |
| POST catalog/issues/confirm/ | Додан бе маҷмӯа |
| GET invoices/ | Иҷораҳо; payment_number дар ҷавоб |
| GET invoices/{id}/ | Ҷузъиёти иҷора ва китобҳо |
| POST invoices/{id}/paid/ | Тасдиқи пурраи нақдӣ, admin/accountant |
| GET/POST kits/ | Маҷмӯаҳои ихтиёрӣ |

Сохтани китоб:

```json
{"title":"Математика","grade":10,"year":2025,"quantity":100,"fee":"5.00"}
```

Тасдиқи иҷора:

```json
{"student_id":1,"edition_ids":[1,2],"expected_total":"10.00","token":"ff82562a-e577-4868-9bac-398173ac4f39"}
```

Token-и нав барои амали нав; token-и пешина танҳо барои retry-и ҳамон payload. Тариф/бақия аз нав санҷида мешаванд. payment_number истиноди маҳаллӣ аст, reference UUID барои compatibility нигоҳ дошта шудааст. Endpoint-и банк callback вуҷуд надорад. SMS аз worker-и GSM фиристода мешавад; endpoint-и public send нест.

Route-ҳои editions/, editions/{id}/intake/, editions/{id}/tariff/, issues/preview/, issues/confirm/ ва invoices/{id}/payments/ барои compatibility-и 0.2 бо ваколатҳои пешина нигоҳ дошта шудаанд. UI-и 2.0 аз ҷараёни нави catalog истифода мекунад. Endpoint-и баргардонӣ хориҷ шудааст ва 404 медиҳад.

Импорт аз UI бо session preview/commit иҷро мешавад. CSV-и reports/export/ маблағҳоро як бор барои ҳар invoice медиҳад; ?kind=stock анбор аст.

Барои таҳрири анбор expected_revision-ро аз API хонед ва бо POST баргардонед; revision-и кӯҳна 409 медиҳад, то бақия ё нархи нав аз болояш навишта нашавад.
