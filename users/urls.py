from django.urls import path
from .views import login

app_name = 'users'

urlpatterns = [
    path('sign-in', login, name='sign-in')
]
