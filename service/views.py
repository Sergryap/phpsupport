from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order


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
