from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': (
            'bio', 'profile_picture', 'position', 'company', 'date_of_birth', 'phone_number'
        )}),
    )

admin.site.register(UserProfile, CustomUserAdmin)