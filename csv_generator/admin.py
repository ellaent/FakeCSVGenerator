from django.contrib import admin

from .models import Column, Schema


@admin.register(Schema)
class SchemeAdmin(admin.ModelAdmin):
    pass


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    pass
