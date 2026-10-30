from django.db import migrations

MEMBER_GROUP = "회원 열람 승인"


def create_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.get_or_create(name=MEMBER_GROUP)


def remove_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=MEMBER_GROUP).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ledger", "0002_alter_asset_id"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(create_group, remove_group)]
