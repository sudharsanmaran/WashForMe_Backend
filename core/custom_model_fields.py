from django.core.validators import MinValueValidator
from django.db import models


class PositiveDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [MinValueValidator(0)]
        super().__init__(*args, **kwargs)


class CustomPositiveInteger(models.PositiveIntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [MinValueValidator(1)]
        super().__init__(*args, **kwargs)
