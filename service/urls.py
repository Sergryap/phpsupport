from django.urls import path
from .views import view_index, view_freelancer_orders

app_name = 'service'

urlpatterns = [
    path('', view_index, name='index'),
    path('freelancer_orders/', view_freelancer_orders, name='freelancer_orders')
]
