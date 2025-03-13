from django.contrib import admin
from .models import Subscription
# Register your models here.


@admin.register(Subscription)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'site','email',)
    search_fields = ('email',)
    list_filter = ('site',)