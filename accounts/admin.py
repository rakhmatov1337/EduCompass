from django.contrib import admin

from .models import User, CenterPayment

# Register your models here.


admin.site.register(User)
admin.site.register(CenterPayment)