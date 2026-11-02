from django.contrib.auth.models import Group, User
from django.template.context import BaseContext
from django.test import TestCase, override_settings
from django.urls import reverse

from .membership import MEMBER_GROUP
from .models import Asset


def _copy_context(self):
    # Django 4.2's BaseContext.__copy__ breaks on Python 3.14 when the test client copies template contexts.
    duplicate = object.__new__(type(self))
    duplicate.__dict__ = self.__dict__.copy()
    duplicate.dicts = self.dicts[:]
    return duplicate


BaseContext.__copy__ = _copy_context

# 테스트에서는 collectstatic 결과(manifest) 없이 템플릿을 렌더링한다.
PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})

MARK = "회원 전용 콘텐츠입니다"
PENDING = "가입 승인을 기다리고 있습니다"


@PLAIN_STATIC
class MembersOnlyTests(TestCase):
    """자산관리 · 인생 후반전 · 인생 후반전1은 승인 회원만 본문을 읽는다."""

    pages = [
        ("/asset-management/", "국민연금"),
        ("/experts/national-pension/", "<h5>"),
        ("/second-half/pension/", 'class="sh-layout"'),
        ("/second-half-1/national-pension/", 'class="sh-layout"'),
        ("/second-half/", 'id="shChecks"'),
        ("/second-half-1/", 'id="shChecks"'),
    ]

    def make_user(self, email, member=False, staff=False):
        user = User.objects.create_user(username=email, email=email, password="pw-Test-1234", is_staff=staff)
        if member:
            user.groups.add(Group.objects.get_or_create(name=MEMBER_GROUP)[0])
        return user

    def test_guest_sees_lock_not_body(self):
        for url, body in self.pages:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertContains(r, MARK, msg_prefix=url)
            self.assertNotContains(r, body, msg_prefix=url)
            self.assertIn("no-cache", r.get("Cache-Control", ""), url)

    def test_pending_user_waits(self):
        self.client.force_login(self.make_user("wait@example.com"))
        for url, body in self.pages:
            r = self.client.get(url)
            self.assertContains(r, PENDING, msg_prefix=url)
            self.assertNotContains(r, body, msg_prefix=url)

    def test_member_and_staff_read_everything(self):
        for user in (self.make_user("m@example.com", member=True), self.make_user("s@example.com", staff=True)):
            self.client.force_login(user)
            for url, body in self.pages:
                r = self.client.get(url)
                self.assertContains(r, body, msg_prefix=url)
                self.assertNotContains(r, MARK, msg_prefix=url)

    def test_public_pages_stay_open(self):
        for url in ("/", "/experts/", "/chapter/ch1/", "/privacy-policy/"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertNotContains(r, MARK, msg_prefix=url)

    def test_header_menus_hidden_from_guests_and_pending(self):
        links = ('href="/asset-management/"', 'href="/second-half/"', 'href="/second-half-1/"')
        for url in ("/", "/chapter/ch1/"):
            r = self.client.get(url)
            for link in links:
                self.assertNotContains(r, link, msg_prefix=url)
        self.client.force_login(self.make_user("wait2@example.com"))
        r = self.client.get("/")
        for link in links:
            self.assertNotContains(r, link)
        self.client.force_login(self.make_user("m2@example.com", member=True))
        r = self.client.get("/")
        for link in links:
            self.assertContains(r, link, count=2)  # 데스크톱 + 모바일 메뉴

    def test_header_logout_button(self):
        self.assertNotContains(self.client.get("/"), 'class="header-logout"')
        self.client.force_login(self.make_user("out@example.com"))
        self.assertContains(self.client.get("/"), 'class="header-logout"', count=2)
        r = self.client.post("/accounts/logout/", {"next": "/"})
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertNotContains(self.client.get("/"), 'class="header-logout"')


@PLAIN_STATIC
class AssetApiTests(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(name="예금", category="deposit", amount=1000)

    def test_guest_and_member_cannot_use_api(self):
        member = User.objects.create_user(username="m@example.com", password="pw-Test-1234")
        member.groups.add(Group.objects.get_or_create(name=MEMBER_GROUP)[0])
        for login in (None, member):
            if login:
                self.client.force_login(login)
            self.assertEqual(self.client.get("/asset-management/api/assets/").status_code, 403)
            self.assertEqual(self.client.post("/asset-management/api/assets/", "{}", content_type="application/json").status_code, 403)
            self.assertEqual(self.client.delete(f"/asset-management/api/assets/{self.asset.pk}/").status_code, 403)
        self.assertTrue(Asset.objects.filter(pk=self.asset.pk).exists())

    def test_staff_can_use_api(self):
        self.client.force_login(User.objects.create_user(username="s@example.com", password="pw-Test-1234", is_staff=True))
        self.assertEqual(self.client.get("/asset-management/api/assets/").status_code, 200)
        self.assertEqual(self.client.delete(f"/asset-management/api/assets/{self.asset.pk}/").status_code, 200)


@PLAIN_STATIC
class SignupLoginTests(TestCase):
    def test_signup_then_back_to_page(self):
        r = self.client.post(reverse("ledger:signup"), {
            "name": "홍길동", "email": "Hong@Example.com", "password1": "safe-pass-9876",
            "password2": "safe-pass-9876", "agree": "on", "next": "/second-half-1/",
        })
        self.assertRedirects(r, "/accounts/signup/done/?next=/second-half-1/", fetch_redirect_response=False)
        user = User.objects.get(username="hong@example.com")
        self.assertFalse(user.groups.exists())
        r = self.client.get(r["Location"])
        self.assertContains(r, 'href="/second-half-1/"')

    def test_login_redirects_to_next_and_rejects_outside(self):
        User.objects.create_user(username="a@example.com", password="safe-pass-9876")
        r = self.client.post(reverse("ledger:login"), {"username": "A@example.com", "password": "safe-pass-9876", "next": "/asset-management/"})
        self.assertRedirects(r, "/asset-management/", fetch_redirect_response=False)
        self.client.logout()
        r = self.client.post(reverse("ledger:login"), {"username": "a@example.com", "password": "safe-pass-9876", "next": "https://evil.example/"})
        self.assertRedirects(r, reverse("ledger:second_half"), fetch_redirect_response=False)

    def test_logout_returns_to_same_page(self):
        self.client.force_login(User.objects.create_user(username="a@example.com", password="x"))
        r = self.client.post(reverse("ledger:logout"), {"next": "/second-half-1/"})
        self.assertRedirects(r, "/second-half-1/", fetch_redirect_response=False)
