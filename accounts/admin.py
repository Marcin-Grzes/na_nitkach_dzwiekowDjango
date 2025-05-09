from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import GuestUser, UserProfile
from events.models import Rezerwations


# Register your models here.
# Inline dla rezerwacji GuestUser
class GuestReservationInline(admin.TabularInline):
    model = Rezerwations
    fk_name = 'guest'
    extra = 0
    readonly_fields = ['event', 'status', 'participants_count', 'created_at']
    can_delete = False


# Inline dla rezerwacji UserProfile
class UserProfileReservationInline(admin.TabularInline):
    model = Rezerwations
    fk_name = 'user'
    extra = 0
    readonly_fields = ['event', 'status', 'participants_count', 'created_at']
    can_delete = False


# Admin Dla GuestUser
@admin.register(GuestUser)
class GuestUserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone_number', 'created_at', 'has_account']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    inlines = [GuestReservationInline]

    def has_account(self, obj):
        return obj.user is not None
    has_account.boolean = True
    has_account.short_description = 'Posiada konto'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    fields = UserAdmin.fields + (('Dodatkowe informacje', {'fields': ('phone_number', 'was_guest')}),)
    list_display = ['first_name', 'last_name', 'email', 'phone_number', 'is_staff', 'was_guest', 'created_at',
                    'has_account']
    inlines = [UserProfileReservationInline]