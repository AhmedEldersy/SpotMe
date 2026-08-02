# Team Builder API

FastAPI wrapper around `team_builder.py` (لم يتم تعديل منطق الحساب نفسه — فقط تم فصل
دالة `normalize_players` عن `load_players` عشان الـ API تقدر تستخدم بيانات مرفوعة
مباشرة من غير ما تكون موجودة في ملف على الـ disk).

## التشغيل

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

بعد كده افتح: `http://127.0.0.1:8000/docs` (Swagger UI تفاعلي فيه كل الـ endpoints).

## البيانات

الملف `data/players.json` فيه بيانات تجريبية (63 لاعب موزعين على الأربع رياضات:
football, basketball, handball, volleyball) عشان تقدر تجرب الـ API على طول.

## Endpoints

| Method | Path                     | الوظيفة |
|--------|--------------------------|---------|
| GET    | `/health`                | فحص إن السيرفر شغال + عدد اللاعبين المحمّلين |
| GET    | `/sports`                | قائمة الرياضات المدعومة، التشكيلات، ومفاتيح التقييم |
| POST   | `/players`               | رفع/استبدال قائمة اللاعبين (JSON list) في الذاكرة |
| GET    | `/players?sport=`        | عرض اللاعبين المحمّلين حاليًا (فلترة اختيارية بالرياضة) |
| POST   | `/players/load-from-disk`| تحميل `data/players.json` من الـ disk للذاكرة |
| POST   | `/team/build`            | بناء تشكيلة لرياضة واحدة |
| POST   | `/team/build-all`        | بناء عدة تشكيلات لعدة رياضات في نداء واحد (زي `main()` الأصلية) |

## مثال سريع

```bash
# 1) حمّل بيانات اللاعبين التجريبية
curl -X POST http://127.0.0.1:8000/players/load-from-disk

# 2) ابنِ تشكيلة كرة قدم
curl -X POST http://127.0.0.1:8000/team/build \
  -H "Content-Type: application/json" \
  -d '{"sport":"football","formation":"4-3-3","play_style":"possession-based attacking football","avg_age_target":26}'
```

## اختبارات

تم اختبار كل الـ endpoints (نجاح وحالات خطأ: رياضة غير معروفة، تشكيلة غير معروفة،
عدم وجود بيانات محمّلة) باستخدام `fastapi.testclient.TestClient` وكلها اشتغلت
بالشكل المتوقع.

**ملاحظة:** رفع لاعب واحد بـ `POST /players` بيستبدل كل القائمة المحمّلة (مش بيضيف
عليها) — لو عايز تضيف فوق البيانات الموجودة، اجمع القايمتين قبل الإرسال.
