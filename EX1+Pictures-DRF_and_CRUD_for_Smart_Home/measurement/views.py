# TODO: опишите необходимые обработчики, рекомендуется использовать generics APIView классы:
# TODO: ListCreateAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework import generics
from .models import Sensor, Measurement
# ======ДОПОЛНИТЕЛЬНО ПО ЗАДАНИЮ
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
# ================================
from .serializers import (
    SensorSerializer,
    SensorDetailSerializer,
    MeasurementSerializer,
)


class SensorListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/sensors/  -> список датчиков (id, name, description)
    POST /api/v1/sensors/  -> создать датчик (name, description?)
    """
    queryset = Sensor.objects.all().order_by('id')
    serializer_class = SensorSerializer


class SensorRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/sensors/<id>/ -> полная инфа о датчике + все измерения
    PATCH /api/v1/sensors/<id>/ -> изменить name/description
    PUT   /api/v1/sensors/<id>/ -> обновить name/description
    """
    queryset = Sensor.objects.all()
    serializer_class = SensorDetailSerializer  # на чтение отдаём detail

    # чтобы PATCH/PUT принимали простую форму (без measurements),
    # переключим сериализатор на "короткий" при записи:
    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return SensorSerializer
        return SensorDetailSerializer


class MeasurementCreateView(generics.CreateAPIView):
    """
    POST /api/v1/measurements/ -> добавить измерение (sensor, temperature)
    """
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser) #ДОПОЛНИТЕЛЬНО ПО ЗАДАНИЮ. Добавляем парсеры для разбора тела запроса.

    # JSONParser — разбирает application / json.
    # Пример: Content - Type: application / json
    # с телом {"sensor": 1, "temperature": 22.3}.
    #
    # MultiPartParser — разбирает multipart / form - data(нужно для загрузки файлов).
    # Пример: -F "image=@photo.jpg" - F "sensor=1" в curl.Файлы окажутся в request.FILES, остальные
    # поля — в request.data.
    #
    # FormParser — разбирает application / x - www - form - urlencoded(обычные
    # HTML - формы, Browsable API).