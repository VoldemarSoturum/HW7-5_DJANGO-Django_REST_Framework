
---

## Дополнительное задание: прикрепление **картинки** к измерению

Датчики могут прикладывать снимки вместе с измерением температуры. Поле должно быть **опциональным**, чтобы старые датчики продолжали работать без изменений.

### Что добавлено

1. **Модель** (`measurement/models.py`)
   ```python
   class Measurement(models.Model):
       # ...
       image = models.ImageField(
           upload_to='measurements/PICTURES/',  # файлы попадут в MEDIA_ROOT/measurements/PICTURES/
           null=True,                           # в БД может быть NULL
           blank=True,                          # поле не обязательно в формах/сериализаторах
       )
   ```

2. **Сериализатор** (`measurement/serializers.py`)
   ```python
   class MeasurementSerializer(serializers.ModelSerializer):
       class Meta:
           model = Measurement
           fields = ['sensor', 'temperature', 'created_at', 'image']
           read_only_fields = ['created_at']
   ```

3. **Вьюха** (`measurement/views.py`) — разрешаем multipart
   ```python
   from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

   class MeasurementCreateView(generics.CreateAPIView):
       queryset = Measurement.objects.all()
       serializer_class = MeasurementSerializer
       parser_classes = (JSONParser, MultiPartParser, FormParser)
   ```

4. **Настройки медиа** (`smart_home/settings.py`)
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```

5. **Раздача медиа в dev** (`smart_home/urls.py`)
   ```python
   from django.conf import settings
   from django.conf.urls.static import static

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('api/', include('measurement.urls')),
   ]

   if settings.DEBUG:
       urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

6. **Миграции**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Как отправлять измерение с картинкой

#### Вариант A — `requests.http` (VS Code REST Client)

```http
@baseUrl = http://localhost:8000/api

### Добавить измерение с картинкой (multipart/form-data)
POST {{baseUrl}}/measurements/
Content-Type: multipart/form-data; boundary=BOUND

--BOUND
Content-Disposition: form-data; name="sensor"

1
--BOUND
Content-Disposition: form-data; name="temperature"

22.7
--BOUND
Content-Disposition: form-data; name="image"; filename="photo.jpg"
Content-Type: image/jpeg

< ./assets/photo.jpg
--BOUND--
```

> Можно указывать относительный путь к файлу (как выше) или абсолютный.  
> В ответе поле `image` вернёт URL вида `/media/measurements/PICTURES/photo.jpg` (или абсолютный, если сериализатор получил `context={'request': request}`).

#### Вариант B — `curl`

```bash
curl -i -X POST http://localhost:8000/api/measurements/ \
  -H "Accept: application/json" \
  -F "sensor=1" \
  -F "temperature=22.7" \
  -F "image=@./assets/photo.jpg"
```

### Ожидаемые ответы

**Успех (с изображением):**
```json
{
  "sensor": 1,
  "temperature": 22.7,
  "created_at": "2025-10-25T19:43:03.318228Z",
  "image": "/media/measurements/PICTURES/photo.jpg"
}
```

**Успех (без изображения):**
```json
{
  "sensor": 1,
  "temperature": 22.3,
  "created_at": "2025-10-25T19:43:03.318228Z",
  "image": null
}
```

### Тест (опционально)

```python
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

def _fake_image(fmt="JPEG", size=(64, 64)):
    f = io.BytesIO()
    Image.new("RGB", size, (200, 100, 50)).save(f, fmt)
    f.seek(0)
    return f.getvalue()

def test_add_measurement_with_image(self):
    sensor = Sensor.objects.create(name="ESP32", description="Кухня")
    img = SimpleUploadedFile("test.jpg", _fake_image(), content_type="image/jpeg")
    resp = self.client.post("/api/measurements/", data={
        "sensor": sensor.id, "temperature": 23.1, "image": img
    }, format="multipart")
    assert resp.status_code == 201
    assert "image" in resp.data
```

### FAQ / Траблшутинг

- **404 при открытии `/media/...`** → добавьте `static(settings.MEDIA_URL, ...)` в корневые `urls.py` и убедитесь, что файл лежит в `MEDIA_ROOT/measurements/PICTURES/`.
- **`415 Unsupported Media Type`** → проверьте `parser_classes` и заголовки запроса.
- **Полный URL в ответе** → передайте `request` в контекст сериализатора (обычно DRF делает это сам в generic CBV).

---

## Скриншоты (дополнение)

> Добавьте сюда иллюстрации по новой функциональности:
>
> - **Multipart запрос с изображением (requests.http)**  
>   ![req-measurement-multipart](docs/img/req-measurement-multipart.png)
>
> - **Ответ сервера с полем image**  
>   ![resp-measurement-image](docs/img/resp-measurement-image.png)
>
> - **Открытие файла по URL /media/...**  
>   ![open-media-url](docs/img/open-media-url.png)

---

## Диаграмма БД (обновлённая)

> Вставьте ER-диаграмму, где у `Measurement` есть опциональное `image: ImageField`:
>
> ![db-diagram-with-image](docs/img/db-diagram-with-image.png)

---

## Скриншоты наполненной базы данных

> Снимки таблиц/админки с несколькими датчиками и измерениями (с картинками и без):
>
> - **Таблица Sensor**  
>   ![db-sensor-sample](docs/img/db-sensor-sample.png)
> - **Таблица Measurement**  
>   ![db-measurement-sample](docs/img/db-measurement-sample.png)
