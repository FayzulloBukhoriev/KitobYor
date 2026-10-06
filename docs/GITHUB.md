# Ба GitHub гузоштани версияи 2.0

Ин дафъа push аз тарафи агент анҷом дода нашудааст. ZIP source-и KitobYor дорад. Барои нигоҳ доштани таърихи commit метавонед файли ҳамроҳи KitobYor-history.bundle-ро истифода кунед.

Дар терминал аз ҷузвдоне, ки bundle ҳаст:

```powershell
git clone KitobYor-history.bundle KitobYor-git
```

```powershell
cd KitobYor-git
```

```powershell
git remote set-url origin https://github.com/FayzulloBukhoriev/KitobYor.git
```

```powershell
git fetch origin
```

```powershell
git push -u origin main
```

GitHub метавонад login талаб кунад. Агар push бо non-fast-forward рад шавад, force push накунед: аввал тағйироти нави remote-ро гирифта, conflict-ро ҳал кунед. Агар checkout-и мавҷудаи repo доред, .git-ро нигоҳ доред; кодҳои 2.0-ро ба он гузаронед ва git diff-ро пеш аз commit бинед. Файлҳои templates/library/returns.html ва edition.html дар 2.0 хориҷ шудаанд. .env ва local_data-ро иваз накунед.

Барои demo README.md-ро хонед. Code ZIP .git надорад; bundle таърихро барқарор мекунад. Маълумоти demo-и худ, .env ва .venv ба repo push нашаванд; .gitignore мавҷуд аст.
