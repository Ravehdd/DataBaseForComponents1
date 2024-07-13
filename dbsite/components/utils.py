from .models import *
from django.db.models import *


class DataMixin:

    def get_user_context(self, **kwargs):
        context = kwargs
        components = Components.objects.all()
        devices = Devices.objects.all()
        connection = Connection.objects.all()
        cats = Category.objects.all()
        return context

