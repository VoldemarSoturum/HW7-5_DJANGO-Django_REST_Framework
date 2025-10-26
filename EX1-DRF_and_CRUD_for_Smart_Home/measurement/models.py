from django.db import models

# TODO: опишите модели датчика (Sensor) и измерения (Measurement)

class Sensor(models.Model):
    # Название датчика. Ограничено 100 символами.
    name = models.CharField(max_length=30)
    # Краткое описание/расположение. Поле необязательное (blank=True),
    # при отсутствии значения в БД будет сохранена пустая строка (default='').
    description = models.CharField(max_length=50, blank=True, default='')

    def __str__(self):
        # Удобное строковое представление в админке/шелле
        # Например: "3: ESP32"
        return f'{self.id}: {self.name}'


class Measurement(models.Model):
    # Связь "многие-к-одному" с Sensor.
    # on_delete=models.CASCADE — при удалении датчика удалятся и его измерения.
    # related_name='measurements' — позволит обращаться к измерениям как sensor.measurements.all()
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='measurements',
    )
    # Температура в градусах Цельсия. FloatField — число с плавающей точкой.
    # (Если нужна фиксированная точность — можно заменить на DecimalField.)
    temperature = models.FloatField()
    # Дата/время создания записи. Проставляется автоматически один раз при вставке.
    created_at = models.DateTimeField(auto_now_add=True)  # время фиксации измерения

    def __str__(self):
        # Пример: "sensor=1 t=22.5 at=2025-10-25 12:34:56+00:00"
        return f'sensor={self.sensor_id} t={self.temperature} at={self.created_at}'
