from django.contrib import admin
from service.models import Order
from users.models import User, Freelancer, Customer
# Register your models here.

admin.site.register(Order)
admin.site.register(User)
admin.site.register(Freelancer)
admin.site.register(Customer)
