from django.contrib import admin
from .models import Order
from users.models import User, Customer, Freelancer


admin.site.register(Order)
admin.site.register(User)
admin.site.register(Customer)
admin.site.register(Freelancer)