from rest_framework import serializers

# TODO: опишите необходимые сериализаторы

from rest_framework import serializers
from .models import Sensor, Measurement


class SensorSerializer(serializers.ModelSerializer):
    """Краткая информация по датчику: id, name, description"""
    class Meta:
        model = Sensor
        # Поля, которые отдаем/принимаем в "списке датчиков" и при создании/редактировании
        fields = ['id', 'name', 'description']


class MeasurementSerializer(serializers.ModelSerializer):
    """
    Сериализатор для измерений.
    Используется:
      - при создании нового измерения (нужны sensor и temperature),
      - при чтении (возвращаем temperature и время created_at).
    """
    class Meta:
        model = Measurement
        # Включаем внеш. ключ sensor, чтобы уметь создать измерение для конкретного датчика
        # ДОПЛНИТЕЛЬНО ПО ЗАДАНИЮ. DRF сам использует ImageField, будет отдавать URL (если запрошено в request контексте)
        fields = ['sensor', 'temperature', 'created_at','image'] #ДОПОЛНИТЕЛЬНО ПО ЗАДИНИЮ ДОБАВИЛ КАРТИНКИ
        # created_at выставляется автоматически на модели — редактировать нельзя
        read_only_fields = ['created_at']


class SensorDetailSerializer(serializers.ModelSerializer):
    """
    Подробная информация по датчику:
      - собственные поля датчика,
      - список всех его измерений.
    Вложенный сериализатор MeasurementSerializer подключаем в режиме read_only,
    чтобы при GET детальной карточки датчика получить измерения,
    но не пытаться редактировать их прямо через датчик.
    """
    # related_name='measurements' из модели Measurement позволяет так обратиться к связке
    measurements = MeasurementSerializer(read_only=True, many=True)

    class Meta:
        model = Sensor
        # Отдаем всё, что требует ТЗ: id, name, description + вложенный список измерений
        fields = ['id', 'name', 'description', 'measurements']