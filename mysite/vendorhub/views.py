from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http.response import JsonResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib import messages
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta

import stripe
import json
from .models import Vendor, Category, Tag, Product, Rating, OrderDetail
from .forms import ProductForm
# Create your views here.

def index(request):
    products = Product.objects.all()
    return render(request, 'vendorhub/index.html', {'products': products})


def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    return render(request, 'vendorhub/product_detail.html', {'product': product})


def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'vendorhub/buy_product.html', {
        'product': product,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)
    

@csrf_exempt
def create_checkout_session(request, product_id):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            request_data = json.loads(request.body)
            product = get_object_or_404(Product, id=product_id)
            domain_url = 'http://127.0.0.1:8000'  
            stripe.api_key = settings.STRIPE_SECRET_KEY

            # Create a Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                customer_email=request_data['email'],  
                payment_method_types=['card'],  
                mode='payment',
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': product.name,
                            },
                            'unit_amount': int(product.price * 100),  
                        },
                        'quantity': 1,
                    },
                ],
                success_url = request.build_absolute_uri(reverse('payment_success')) + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url = request.build_absolute_uri(reverse('payment_cancelled'))
            )

            # Save the order details
            order = OrderDetail(
            customer_email=request_data['email'],
            product=product,
            amount=product.price,
            stripe_payment_intent=checkout_session.payment_intent  
            )
            order.save()

            # Debugging: Print the order and checkout session details
            print(f"Checkout Session Payment Intent: {checkout_session["payment_intent"]}")
            print(f"Order created with Stripe Payment Intent: {order.stripe_payment_intent}")
            print(f"Order Details: {order}")

            return JsonResponse({'sessionId': checkout_session.id})
        except Exception as e:
            print(f"Error creating checkout session: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


def payment_success(request):
    # Retrieve the session_id from the query parameters
    session_id = request.GET.get('session_id')
    print(f"Session ID: {session_id}")
    if not session_id:
        return HttpResponseNotFound("Session ID not found.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Retrieve the Stripe Checkout Session
        session = stripe.checkout.Session.retrieve(session_id)


        # Debugging: Print the session details
        print(f"Session Payment Intent: {session.payment_intent}")
        print(f"Session Details: {session}")

        # get latest order details
        order = OrderDetail.objects.latest('id')
        
        # Update the stripe_payment_intent field
        order.stripe_payment_intent = session.payment_intent
        order.has_paid = True
        order.save()
        
        print(f"Order updated with Stripe Payment Intent: {order.stripe_payment_intent}")

        # Render the success page
        return render(request, 'vendorhub/payment_success.html', {'order': order})
    except OrderDetail.DoesNotExist:
        print("No orders found.")
        return HttpResponseNotFound("Order not found.")
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        return HttpResponseNotFound("An error occurred while processing your payment.")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return HttpResponseNotFound("An error occurred while processing your payment.")
    

def payment_cancelled(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'vendorhub/payment_cancelled.html', {'product': product})



@login_required
def add_product(request):
    # Check if the user is a vendor
    if not hasattr(request.user, 'vendor'):
        raise PermissionDenied("You are not authorized to add products.")
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Associate the product with the logged-in vendor
            product = form.save(commit=False)
            product.vendor = request.user.vendor
            product.save()
            form.save_m2m()  # Save many-to-many fields (e.g., tags)
            return redirect('index')  # Redirect to the product list page
    else:
        form = ProductForm()
    
    return render(request, 'vendorhub/add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    # Fetch the product to be edited
    product = get_object_or_404(Product, id=product_id)
    
    # Ensure the logged-in vendor owns the product
    if product.vendor != request.user.vendor:
        raise PermissionDenied("You are not authorized to edit this product.")
    
    if request.method == 'POST':
        # Populate the form with the submitted data and the existing product instance
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', product_id = product.id)      # Redirect to the product
    else:
        # Pre-fill the form with the existing product data
        form = ProductForm(instance=product)
    
    return render(request, 'vendorhub/edit_product.html', {
        'form': form,
        'product': product
        })



@login_required
def delete_product(request, product_id):
    # Fetch the product to be deleted
    product = get_object_or_404(Product, id=product_id)
    
    # Ensure the logged-in vendor owns the product
    if product.vendor != request.user.vendor:
        raise PermissionDenied("You are not authorized to delete this product.")
    
    if request.method == 'POST':
        product.delete()
        return redirect('index')  # Redirect to the product list page
    
    return render(request, 'vendorhub/delete_product.html', {'product': product})



@login_required
def vendor_dashboard(request):
    # Check if the user has a vendor profile
    if not hasattr(request.user, 'vendor') or not request.user.profile.is_vendor:
        # If the user is not a vendor, pass a flag to the template
        messages.warning(request, 'You need to be a vendor to access this page.')
        return render(request, 'vendorhub/dashboard.html', {'is_vendor': False})
    
    # Fetch products owned by the logged-in vendor
    products = Product.objects.filter(vendor=request.user.vendor)
    
    # Annotate each product with total earnings and average rating
    products = products.annotate(
        total_earnings=Sum('total_sales_amount'),
        average_rating=Avg('ratings__rating')
    )
    
    # Format total_earnings to 2 decimal places
    for product in products:
        if product.total_earnings is not None and product.average_rating is not None:
            product.total_earnings = round(float(product.total_earnings), 2)
            product.average_rating = round(float(product.average_rating), 1)
    
    context = {
        'products': products,
        'is_vendor': True,  # Indicate that the user is a vendor
    }
    return render(request, 'vendorhub/dashboard.html', context)


@login_required
def order_history(request):
    orders = OrderDetail.objects.filter(customer_email=request.user.email)
    return render(request, 'vendorhub/order_history.html', {'orders': orders})

@login_required
def vendor_sales_analysis(request):
    # Check if the user is a vendot
    if not hasattr(request.user, 'vendor') or not request.user.profile.is_vendor:
        messages.warning(request, 'You need to be a vendor to access this page.')
        return redirect('index')
    
    # Fetch products owned by the logged-in vendor
    products = Product.objects.filter(vendor=request.user.vendor)
    
    # Annotate each product with total orders and total sales
    products = products.annotate(
        total_orders=Count('orders'),  # Count the number of orders for each product
        total_sales_amount_annotation=Sum('orders__amount')  # Sum the amount of all orders for each product
    )

    # Calculate total sales for all products
    total_sales_all_products = OrderDetail.objects.filter(
        product__vendor=request.user.vendor
        ).aggregate(total_sales_amount=Sum('amount'))['total_sales_amount'] or 0

    # Format total sales for each product to 2 decimal places
    for product in products:
        if product.total_sales_amount_annotation is not None:
            product.total_sales_amount_annotation = round(float(product.total_sales_amount_annotation), 2)

    # Format total sales for all products to 2 decimal places
    total_sales_all_products = round(float(total_sales_all_products), 2)
    
    context = {
        'products': products,
        'total_sales_all_products': total_sales_all_products,
    }
    return render(request, 'vendorhub/sales_analysis.html', context)


@login_required
def vendor_sales_dashboard(request):
    # Check if the user is a vendot
    if not hasattr(request.user, 'vendor') or not request.user.profile.is_vendor:
        messages.warning(request, 'You need to be a vendor to access this page.')
        return redirect('index')
    
    # Fetch products owned by the logged-in vendor
    products = Product.objects.filter(vendor=request.user.vendor).annotate(
        total_revenue=Sum('orders__amount') 
    )

    # Calculate total revenue for all products
    total_revenue_all_products = OrderDetail.objects.filter(
        product__vendor=request.user.vendor
    ).aggregate(total_revenue=Sum('amount'))['total_revenue'] or 0
    
    # Calculate total revenue for each month/year
    now = timezone.now()
    monthly_revenue = OrderDetail.objects.filter(
        product__vendor=request.user.vendor
    ).extra(
        {'month': "strftime('%%Y-%%m', created_on)"}
    ).values('month').annotate(total_revenue=Sum('amount')).order_by('month')
    
    yearly_revenue = OrderDetail.objects.filter(
        product__vendor=request.user.vendor
    ).extra(
        {'year': "strftime('%%Y', created_on)"}
    ).values('year').annotate(total_revenue=Sum('amount')).order_by('year')
    
    # Top 5 products by revenue and sales count
    top_5_products_by_revenue = products.order_by('-total_revenue')[:5]
    
    top_5_products_by_sales_count = products.annotate(
        total_sales_count=Count('orders')  # Renamed to avoid conflict
    ).order_by('-total_sales_count')[:5]
    
    # Total revenue generated by each product per month
    product_monthly_revenue = OrderDetail.objects.filter(
        product__vendor=request.user.vendor
    ).extra(
        {'month': "strftime('%%Y-%%m', created_on)"}
    ).values('product__name', 'month').annotate(total_revenue=Sum('amount')).order_by('month')
    
    # Sales trends over time (daily, weekly, monthly)
    daily_sales = OrderDetail.objects.filter(
        product__vendor=request.user.vendor,
        created_on__gte=now - timedelta(days=30)
    ).extra(
        {'day': "strftime('%%Y-%%m-%%d', created_on)"}
    ).values('day').annotate(total_sales=Sum('amount')).order_by('day')
    
    weekly_sales = OrderDetail.objects.filter(
        product__vendor=request.user.vendor,
        created_on__gte=now - timedelta(days=365)
    ).extra(
        {'week': "strftime('%%Y-%%W', created_on)"}
    ).values('week').annotate(total_sales=Sum('amount')).order_by('week')
    
    monthly_sales = OrderDetail.objects.filter(
        product__vendor=request.user.vendor,
        created_on__gte=now - timedelta(days=365)
    ).extra(
        {'month': "strftime('%%Y-%%m', created_on)"}
    ).values('month').annotate(total_sales=Sum('amount')).order_by('month')
    
    # Prepare data for charts
    chart_labels = [product.name for product in products]
    chart_data = [float(product.total_revenue or 0) for product in products]
    
    # Prepare data for pie chart (top 5 products by revenue)
    pie_chart_labels = [product.name for product in top_5_products_by_revenue]
    pie_chart_data = [float(product.total_revenue or 0) for product in top_5_products_by_revenue]
    
    # Prepare data for line chart (sales trends)
    daily_sales_labels = [entry['day'] for entry in daily_sales]
    daily_sales_data = [float(entry['total_sales'] or 0) for entry in daily_sales]
    
    weekly_sales_labels = [entry['week'] for entry in weekly_sales]
    weekly_sales_data = [float(entry['total_sales'] or 0) for entry in weekly_sales]
    
    monthly_sales_labels = [entry['month'] for entry in monthly_sales]
    monthly_sales_data = [float(entry['total_sales'] or 0) for entry in monthly_sales]
    
    context = {
        'products': products,
        'total_revenue_all_products': total_revenue_all_products,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'top_5_products_by_revenue': top_5_products_by_revenue,
        'top_5_products_by_sales_count': top_5_products_by_sales_count,
        'product_monthly_revenue': product_monthly_revenue,
        'daily_sales_labels': daily_sales_labels,
        'daily_sales_data': daily_sales_data,
        'weekly_sales_labels': weekly_sales_labels,
        'weekly_sales_data': weekly_sales_data,
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_data,
    }
    return render(request, 'vendorhub/sales_dashboard.html', context)
