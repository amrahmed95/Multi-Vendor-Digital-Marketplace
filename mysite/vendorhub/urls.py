from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Home page (product list)
    path('products/<int:product_id>', views.product_detail, name='product_detail'),  # Product detail page
    path('products/<int:product_id>/buy', views.buy_product, name='buy_product'),  # Buy product page
    path('add-product', views.add_product, name='add_product'),  # Add product page
    path('edit-product/<int:product_id>', views.edit_product, name='edit_product'),  # Edit product page
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),  # Delete product
    path('success/', views.payment_success, name='payment_success'),  # Payment success page
    path('failed', views.payment_cancelled, name='payment_cancelled'),  # Payment cancelled page
    path('config/', views.stripe_config, name='stripe_config'),  # Stripe public key config
    path('api/create-checkout-session/<int:product_id>/', views.create_checkout_session, name='create_checkout_session'),  # Stripe checkout session
    path('dashboard', views.vendor_dashboard, name='vendor_dashboard'), # Vendor dashboard
    path('orders', views.order_history, name='order_history'), # Order history
    path('sales-analysis', views.vendor_sales_analysis, name='vendor_sales_analysis'), # Sales analysis
    path('sales-dashboard', views.vendor_sales_dashboard, name='vendor_sales_dashboard'), # Sales dashboard
    
]