from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order
from users.models import Freelancer


@login_required(login_url='users:sign-in')
def view_index(request):
    orders = Order.objects.all()
    processed_orders = []
    for order in orders:
        order_attr_for_managers = {
            'id': order.id,
            'title': order.title,
            'customer': order.client,
            'freelancer': order.freelancer,
            'status': order.get_status_display(),
            'created_at': order.created_at,
            'deadline': order.deadline
        }  
        processed_orders.append(order_attr_for_managers)

    return render(request, 'service/index.html', context={
        'processed_orders': processed_orders
    })


@login_required(login_url='users:sign-in')
def view_freelancer_orders(request):
    freelancers = Freelancer.objects.all()
    freelancer_orders = []
    for freelancer in freelancers:
        freelancer_attrs = {
            'username': freelancer.username,
            'orders': len(freelancer.freelancer_orders.all()),
            'phone_number': freelancer.phone_number,
            'rating': freelancer.rating
        }
        freelancer_orders.append(freelancer_attrs)
    
    return render(request, 'service/freelancer_orders.html', context={
        'freelancer_orders': freelancer_orders
    })
