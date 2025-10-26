# Create your tests here.

# measurement/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from measurement.models import Sensor, Measurement
# ============ДОПОЛНИТЕЛЬНО ВВЕЛИ ИМПОРТЫ==============================

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

# ===========================================
class SmartHomeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.base = "/api"  # в корневом urls.py подключено include('measurement.urls') по префиксу /api/

    def test_list_sensors_empty(self):
        """GET /sensors/ — пустой список, 200 OK"""
        resp = self.client.get(f"{self.base}/sensors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertEqual(resp.data, [])

    def test_create_sensor(self):
        """POST /sensors/ — создаёт датчик, 201 Created"""
        payload = {"name": "ESP32", "description": "Кухня"}
        resp = self.client.post(f"{self.base}/sensors/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", resp.data)
        self.assertEqual(resp.data["name"], payload["name"])
        self.assertEqual(resp.data["description"], payload["description"])
        # в БД действительно есть 1 датчик
        self.assertEqual(Sensor.objects.count(), 1)

    def test_update_sensor_patch(self):
        """PATCH /sensors/<id>/ — обновляет только переданные поля, 200 OK"""
        sensor = Sensor.objects.create(name="ESP32", description="Кухня")
        update = {"description": "Балкон"}
        resp = self.client.patch(f"{self.base}/sensors/{sensor.id}/", update, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        self.assertEqual(sensor.description, "Балкон")
        self.assertEqual(sensor.name, "ESP32")  # имя не должно измениться

    def test_add_measurement(self):
        """POST /measurements/ — добавляет измерение, created_at read-only, 201 Created"""
        sensor = Sensor.objects.create(name="ESP32", description="Кухня")
        payload = {"sensor": sensor.id, "temperature": 22.3}
        resp = self.client.post(f"{self.base}/measurements/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # запись действительно создана
        self.assertEqual(Measurement.objects.count(), 1)
        m = Measurement.objects.get()
        self.assertEqual(m.sensor_id, sensor.id)
        self.assertAlmostEqual(m.temperature, 22.3, places=3)
        # created_at должен вернуться в ответе и быть строкой (ISO)
        self.assertIn("created_at", resp.data)
        self.assertIsInstance(resp.data["created_at"], str)

    def test_sensor_detail_includes_measurements(self):
        """GET /sensors/<id>/ — возвращает вложенный список measurements"""
        sensor = Sensor.objects.create(name="ESP32", description="Кухня")
        Measurement.objects.create(sensor=sensor, temperature=22.3)
        Measurement.objects.create(sensor=sensor, temperature=22.5)
        resp = self.client.get(f"{self.base}/sensors/{sensor.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], sensor.id)
        self.assertEqual(resp.data["name"], "ESP32")
        self.assertEqual(resp.data["description"], "Кухня")
        self.assertIn("measurements", resp.data)
        self.assertIsInstance(resp.data["measurements"], list)
        self.assertEqual(len(resp.data["measurements"]), 2)
        # каждый элемент должен содержать temperature и created_at
        for item in resp.data["measurements"]:
            self.assertIn("temperature", item)
            self.assertIn("created_at", item)
#===================ДОПОЛНИТЕЛЬНЫЙ ТЕСТ ПО ЗАДАНИЮ С СОХРАНЕНИЕМ КАРТИНОК/ФОТО С ДАТЧИКОВ

    def _fake_image(self, fmt="JPEG", size=(64, 64), color=(200, 100, 50)):
        # Создаём "файл" в памяти — буфер байт, который ведет себя как открытый файл.
        f = io.BytesIO()
        # Рисуем простое изображение указанного размера и цвета (нужна Pillow).
        img = Image.new("RGB", size, color)
        # Сохраняем картинку в буфер в формате fmt (по умолчанию JPEG).
        img.save(f, fmt)
        # Перемещаем курсор буфера в начало, чтобы дальше читать с нуля.
        f.seek(0)
        # Возвращаем сырые байты изображения — это удобнее для SimpleUploadedFile.
        return f.getvalue()

    def test_add_measurement_with_image(self):
        # Готовим связанный объект: датчик, к которому прикрепим измерение.
        sensor = Sensor.objects.create(name="ESP32", description="Кухня")

        # Генерируем «фейловую» картинку-байты в памяти.
        img_bytes = self._fake_image()

        # Заворачиваем байты в объект, имитирующий загруженный пользователем файл.
        # Первый аргумент — имя файла (будет использовано как filename),
        # второй — содержимое, content_type должен соответствовать формату (image/jpeg).
        file = SimpleUploadedFile("test.jpg", img_bytes, content_type="image/jpeg")

        # Отправляем POST на эндпоинт создания измерения.
        # format="multipart" => клиент DRF соберёт multipart/form-data,
        # чтобы передать и обычные поля, и файл.
        resp = self.client.post(
            "/api/measurements/",
            data={"sensor": sensor.id, "temperature": 23.1, "image": file},
            format="multipart",
        )

        # Ожидаем успешное создание записи.
        self.assertEqual(resp.status_code, 201)

        # В ответе должно присутствовать поле image (путь/URL к сохранённому файлу).
        self.assertIn("image", resp.data)

        # Проверяем, что это либо относительный медиа-путь (dev),
        # либо абсолютный URL (если сериализатор формирует полные ссылки).
        self.assertTrue(
            str(resp.data["image"]).startswith("/media/") or
            "http" in str(resp.data["image"])
        )
# ===========================================================================