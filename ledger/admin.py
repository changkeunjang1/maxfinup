from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "amount", "acquired_on", "updated_at")
    list_filter = ("category",)
    search_fields = ("name", "memo")
