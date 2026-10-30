from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User

from .membership import MEMBER_GROUP
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "amount", "acquired_on", "updated_at")
    list_filter = ("category",)
    search_fields = ("name", "memo")


admin.site.unregister(User)


@admin.register(User)
class MemberUserAdmin(UserAdmin):
    """회원 목록에서 회원 전용 메뉴(자산관리 · 인생 후반전 · 인생 후반전1) 열람 승인·해제를 한 번에 한다."""

    list_display = ("email", "first_name", "is_member", "date_joined", "last_login", "is_staff")
    list_filter = ("groups", "is_staff", "is_active")
    ordering = ("-date_joined",)
    actions = ["approve_members", "revoke_members"]

    @admin.display(boolean=True, description="열람 승인")
    def is_member(self, obj):
        return obj.is_staff or obj.groups.filter(name=MEMBER_GROUP).exists()

    @admin.action(description="선택한 회원 — 회원 전용 메뉴 열람 승인")
    def approve_members(self, request, queryset):
        group, _ = Group.objects.get_or_create(name=MEMBER_GROUP)
        for user in queryset:
            user.groups.add(group)
        self.message_user(request, f"{queryset.count()}명을 승인했습니다.", messages.SUCCESS)

    @admin.action(description="선택한 회원 — 열람 승인 해제")
    def revoke_members(self, request, queryset):
        group = Group.objects.filter(name=MEMBER_GROUP).first()
        if group:
            for user in queryset:
                user.groups.remove(group)
        self.message_user(request, f"{queryset.count()}명의 승인을 해제했습니다.", messages.WARNING)
