from django.db import models


class Asset(models.Model):
    CATEGORY_CHOICES = [
        ("real_estate", "부동산"),
        ("deposit", "예금·적금"),
        ("securities", "주식·펀드"),
        ("insurance", "보험"),
        ("vehicle", "차량·장비"),
        ("cash", "현금성자산"),
        ("other", "기타"),
    ]

    name = models.CharField("자산명", max_length=100)
    category = models.CharField("분류", max_length=20, choices=CATEGORY_CHOICES, default="other")
    amount = models.DecimalField("평가금액", max_digits=15, decimal_places=0)
    acquired_on = models.DateField("취득일", null=True, blank=True)
    memo = models.CharField("메모", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-amount", "-created_at"]

    def __str__(self):
        return self.name
