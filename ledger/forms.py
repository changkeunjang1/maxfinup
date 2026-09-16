from django import forms

from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "category", "amount", "acquired_on", "memo"]
        widgets = {
            "acquired_on": forms.DateInput(attrs={"type": "date"}),
        }
