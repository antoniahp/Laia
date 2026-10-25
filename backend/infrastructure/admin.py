from django.contrib import admin

from domain.entities import Account, Business, Order


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "phone", "country", "language", "status", "verified_by", "created_at")
    list_filter = ("status", "source", "country", "language")
    search_fields = ("name", "phone")
    list_editable = ("status",)
    readonly_fields = ("source", "google_place_id", "created_at")
    actions = ["verify", "reject"]

    @admin.action(description="Verificar los negocios seleccionados")
    def verify(self, request, queryset):
        queryset.update(status=Business.VERIFIED, verified_by="admin")

    @admin.action(description="Rechazar los negocios seleccionados")
    def reject(self, request, queryset):
        queryset.update(status=Business.REJECTED, verified_by="admin")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("business_name", "account", "status", "mode", "created_at")
    list_filter = ("status", "mode")
    search_fields = ("business_name", "account__email")
    exclude = ("call_secret",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in Order._meta.fields if f.name not in ("status", "call_secret")]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_admin", "telegram_chat_id", "created_at")
    list_filter = ("is_admin",)
    search_fields = ("email", "name")
    exclude = ("password_hash", "telegram_link_code")
