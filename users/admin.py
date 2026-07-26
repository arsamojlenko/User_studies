from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Group Assignment'
    fields = ('condition',)          # Only show the condition field
    extra = 0

class RestrictedUserAdmin(UserAdmin):
    # Only show these columns in the user list
    list_display = ('username', 'get_condition', 'is_staff', 'is_active')
    list_filter = ('profile__condition', 'is_staff', 'is_active')
    search_fields = ('username',)

    # Remove the ability to change password and see most fields
    fieldsets = (
        (None, {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
    )

    # When adding a new user, keep it simple
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    inlines = (ProfileInline,)

    # Hide the "Change password" link
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing user
            return ('username',)
        return ()

    def get_condition(self, obj):
        try:
            return obj.profile.get_condition_display()
        except Profile.DoesNotExist:
            return "No profile"
    get_condition.short_description = 'Group'

# Unregister the original User admin and register our restricted version
admin.site.unregister(User)
admin.site.register(User, RestrictedUserAdmin)