from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from tickets.models import Booking, Category, Event, Seat, Ticket, User, Venue


@admin.register(User)
class HalcyonUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("API role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("API role", {"fields": ("role",)}),)


# Transactional booking changes go through the API, including cancellations.
@admin.register(Booking, Ticket)
class ReservationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register([Venue, Seat, Category, Event])
