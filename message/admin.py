from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'site', 'name', 'email', 'subject')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('site',)
