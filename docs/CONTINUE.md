# Идома аз KitobYor 1.0

Аввал docs/PROGRESS.md ва README.md, баъд git status ва branch/SHA-ро хон. Лоиҳа Django/DRF, PostgreSQL; frontend server-rendered HTML/CSS/JS. Demo бе Docker бо run_demo.py ва SQLite-и ошкор. Register-и оммавӣ нест.

User version 1.0 ZIP гирифт, ин turn агент GitHub push накард. Origin: https://github.com/FayzulloBukhoriev/KitobYor.git. Барои версияи воқеии баъдӣ checkout-и repo-и user-ро манбаъ гир, аз seed/ZIP-и пешина overwrite накун.

Қоидаҳои нави UI: codes/publisher/ISBN/library language input нест; гурӯҳ select A–E; catalog quantity+fee; issue аз китобҳои синфи хонанда бо checkbox ва year/price; kit ихтиёрӣ; рақами payment маҳаллӣ; SMS танҳо preview; cash «Пардохт шуд» finance; returns UI/API нест; reports invoice totals як бор дар CSV.

Ҳифз кун: tenant scope/roles/CSRF, atomic stock/loan/invoice/outbox, Decimal snapshots, UUID retry, school/stock row locks, audited quantity edits, migration-и 0.2, маълумоти шахсӣ. .env/local_data/.venv ба Git нараванд. Initial migration-ро reset накун. Базаи demo-и user-ро ҳазф накун. Пардохти бонк ва SMS-и воқеиро бе API/specification иддао накун.

44 tests passed; 2 PostgreSQL concurrency skipped маҳаллӣ. Тестҳои гузаштаро танҳо барои тағйироти вобаста/хатои нав такрор кун. Барои коркарди оянда migration-и нав соз. Кодро пурра дар чат набарор; як агент, progress-и кӯтоҳ ва checkpoint-и нав. Ҳар қисми анҷомёфта commit шавад. README роҳи оғоз дорад.
