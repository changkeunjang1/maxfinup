from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "category", "amount", "acquired_on", "memo"]
        widgets = {
            "acquired_on": forms.DateInput(attrs={"type": "date"}),
        }


class EmailLoginForm(AuthenticationForm):
    """이메일(= username) 또는 아이디(admin, cgjang 같은 관리 계정)로 로그인. 이메일은 대소문자 구분 없이 받는다."""

    username = forms.CharField(label="이메일 또는 아이디", max_length=150,
                               widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True, "autocapitalize": "none"}))
    password = forms.CharField(label="비밀번호", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    error_messages = {
        "invalid_login": "이메일(아이디) 또는 비밀번호가 올바르지 않습니다.",
        "inactive": "사용이 중지된 계정입니다. 관리자에게 문의해 주세요.",
    }

    def clean_username(self):
        name = self.cleaned_data["username"].strip()
        return name.lower() if "@" in name else name


class SignupForm(forms.Form):
    name = forms.CharField(label="이름", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(label="이메일", max_length=150, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1 = forms.CharField(label="비밀번호", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
                                help_text="8자 이상, 숫자만으로 된 비밀번호는 쓸 수 없습니다.")
    password2 = forms.CharField(label="비밀번호 확인", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    agree = forms.BooleanField(label="개인정보 수집·이용에 동의합니다. (필수)",
                               error_messages={"required": "개인정보 수집·이용에 동의해야 가입할 수 있습니다."})

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("이미 가입된 이메일입니다. 로그인해 주세요.")
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "비밀번호가 서로 다릅니다.")
        elif p1:
            probe = User(username=data.get("email") or "", email=data.get("email") or "", first_name=data.get("name") or "")
            try:
                password_validation.validate_password(p1, probe)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return data

    def save(self):
        d = self.cleaned_data
        return User.objects.create_user(username=d["email"], email=d["email"], password=d["password1"], first_name=d["name"])
