"""
Запускать после каждой правки data.json:
    python make_manifest.py

Что делает:
1. Проверяет, что data.json — правильный JSON и в нём есть модели.
2. Проверяет, что все ссылки моделей на группы (families) существуют.
3. Увеличивает version, если данные изменились.
4. Считает SHA-256 файла и пишет manifest.json.
Приложение сравнивает эту сумму со своей и качает data.json только при изменении.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

here = Path(__file__).parent
data_path = here / "data.json"
manifest_path = here / "manifest.json"

raw = data_path.read_bytes()
try:
    data = json.loads(raw.decode("utf-8"))
except Exception as e:
    sys.exit(f"ОШИБКА: data.json не читается как JSON: {e}")

models = data.get("models") or []
families = {f["id"] for f in data.get("families") or []}
if not models:
    sys.exit("ОШИБКА: в data.json нет моделей")

problems = []
ids = set()
for m in models:
    for key in ("id", "brand", "model"):
        if not m.get(key):
            problems.append(f"модель без поля {key}: {m}")
    if m.get("id") in ids:
        problems.append(f"повтор id: {m.get('id')}")
    ids.add(m.get("id"))
    for fam in m.get("families", []):
        if fam not in families:
            problems.append(f"{m.get('id')}: нет группы '{fam}' в families")
if problems:
    sys.exit("ОШИБКИ:\n  " + "\n  ".join(problems))

old = {}
if manifest_path.exists():
    old = json.loads(manifest_path.read_text(encoding="utf-8"))

sha = hashlib.sha256(raw).hexdigest()
if old.get("sha256") == sha:
    print(f"Данные не изменились (версия {old.get('version')}), manifest оставлен как есть.")
    sys.exit(0)

version = int(old.get("version", 0)) + 1
manifest = {
    "version": version,
    "sha256": sha,
    "models": len(models),
    "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"Готово: версия {version}, моделей {len(models)}, sha256 {sha[:12]}…")
print("Теперь загрузи data.json и manifest.json на сервер (git commit + push).")
