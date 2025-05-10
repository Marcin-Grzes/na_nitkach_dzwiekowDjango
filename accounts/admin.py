from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import GuestUser, UserProfile
from events.models import Rezerwations


# Register your models here.

# ========= GuestUser =========

# Inline dla rezerwacji GuestUser
class GuestReservationInline(admin.TabularInline):
    model = Rezerwations
    fk_name = 'guest'
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


# ========= UserProfile =========


# Rezerwacje użytkowników (nie profile)
class UserReservationInline(admin.TabularInline):
    model = Rezerwations
    fk_name = 'user'  # Rezerwacje są przypisane do User, nie do UserProfile
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


# Admin dla UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_full_name', 'get_email', 'phone_number', 'was_guest']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone_number']
    # inlines = [UserReservationInline]  # Dodajemy rezerwacje użytkownika

    def get_username(self, obj):
        return obj.user.username

    get_username.short_description = 'Nazwa użytkownika'

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_full_name.short_description = 'Imię i nazwisko'

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'
