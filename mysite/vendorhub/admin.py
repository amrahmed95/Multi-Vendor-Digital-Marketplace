from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Vendor)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Product)
admin.site.register(Rating)
admin.site.register(OrderDetail)


