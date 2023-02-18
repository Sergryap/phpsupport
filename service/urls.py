from django.urls import path
from .views import view_index

app_name = 'service'

urlpatterns = [
    path('', view_index, name='index'),
]
