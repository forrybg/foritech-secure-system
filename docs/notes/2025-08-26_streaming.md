# Foritech Project Note — 2025-08-26 (Streaming & CI)

**Дата:** 2025-08-26  
**Автор:** forrybg  
**Версия:** v1.0

## Резюме
Стриймингът (chunked AEAD) е интегриран; CLI има авто-режим ≥64 MiB и нови флагове.
CI е пиннат на Python 3.12 и минава зелено.

## Контекст
- Проект/модул: foritech (SDK/CLI)
- Branch/tag: main
- Обхват: streaming ядро + CLI auto-stream + CI

## Постигнато
- [x] Streaming ядро (Kyber768 + ChaCha20-Poly1305)
- [x] CLI авто-стрийминг ≥64 MiB; флагове --stream/--no-stream/--stream-threshold-mib
- [x] 128 MiB стрес тест: SHA256 OK
- [x] CI изчистен и зелен

## Взети решения
| Тема | Решение | Причина | Влияние |
|---|---|---|---|
| Threshold | 64 MiB | Баланс RAM/скорост | Без промяна за малки файлове |
| AAD | header_json + idx | Силен bind към метаданни и ред | Надеждност при стрийм |

## Блокери / Рискове
- Наличност на liboqs/python на CI runners → stream тестовете са локални засега

## Следващи стъпки
**Днес:**
- README секция + PDF

**Следващи 2–3 дни:**
- Негативни тестове (счупен header, грешен ключ)
- FastAPI demo

**Следваща седмица:**
- PyPI (lite) + Docker образ

## CI/Автоматизация
- CI • 3.12 (pytest) → зелено
- CI • Lite (lint/discover) → зелено

## Метрики / Тестове
- 128 MiB streaming wrap+unwrap: OK (~2s локално)

## Артефакти/Линкове
- scripts/stream_roundtrip.py
