from django.db import migrations, models
from django.db.models import deletion
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.AutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID")),
                ("username", models.CharField(
                    max_length=25, unique=True,
                    verbose_name="имя пользователя")),
                ("access_token", models.CharField(
                    blank=True, max_length=40, verbose_name="токен доступа")),
                ("is_oldfag", models.BooleanField(
                    default=False, verbose_name="старый участник",
                    help_text="Отметьте, чтобы снять ограничение кармы.")),
                ("is_banned", models.BooleanField(
                    default=False, verbose_name="забанен")),
                ("first_login", models.DateTimeField(
                    default=timezone.now, verbose_name="первый вход")),
                ("last_login", models.DateTimeField(
                    blank=True, null=True, verbose_name="последний вход")),
            ],
            options={
                "verbose_name": "пользователь",
                "verbose_name_plural": "пользователи",
                "ordering": ["username"],
            },
        ),
        migrations.CreateModel(
            name="Mail",
            fields=[
                ("id", models.AutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID")),
                ("body", models.TextField(max_length=400)),
                ("send_date", models.DateTimeField(
                    db_index=True, default=timezone.now)),
                ("read_date", models.DateTimeField(
                    blank=True, db_index=True, null=True)),
            ],
            options={
                "ordering": ["send_date"],
            },
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                ("id", models.AutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID")),
                ("fullname", models.CharField(
                    max_length=80, verbose_name="полное имя")),
                ("postcode", models.CharField(
                    max_length=20, verbose_name="индекс")),
                ("address", models.TextField(
                    max_length=200, verbose_name="адрес")),
                ("gift_sent", models.DateTimeField(
                    blank=True, db_index=True, null=True,
                    verbose_name="подарок отправлен")),
                ("gift_received", models.DateTimeField(
                    blank=True, db_index=True, null=True,
                    verbose_name="подарок получен")),
                ("giftee", models.OneToOneField(
                    blank=True, null=True, on_delete=deletion.CASCADE,
                    related_name="santa", to="clubadm.Member",
                    verbose_name="получатель подарка")),
            ],
            options={
                "verbose_name": "участник",
                "verbose_name_plural": "участники",
                "ordering": ["season", "fullname"],
            },
        ),
        migrations.CreateModel(
            name="Season",
            fields=[
                ("year", models.IntegerField(
                    primary_key=True, serialize=False, verbose_name="год")),
                ("gallery", models.URLField(
                    blank=True, verbose_name="пост хвастовства подарками")),
                ("signups_start", models.DateField(
                    verbose_name="начало регистрации")),
                ("signups_end", models.DateField(
                    verbose_name="жеребьевка адресов")),
                ("ship_by", models.DateField(
                    help_text="После этой даты сезон закрывается и уходит вархив.",
                    verbose_name="последний срок отправки подарка")),
            ],
            options={
                "verbose_name": "сезон",
                "verbose_name_plural": "сезоны",
                "ordering": ["year"],
                "get_latest_by": "year",
            },
        ),
        migrations.AddField(
            model_name="member",
            name="season",
            field=models.ForeignKey(
                on_delete=deletion.CASCADE, to="clubadm.Season",
                verbose_name="сезон"),
        ),
        migrations.AddField(
            model_name="member",
            name="user",
            field=models.ForeignKey(
                on_delete=deletion.CASCADE, to="clubadm.User",
                verbose_name="пользователь"),
        ),
        migrations.AddField(
            model_name="mail",
            name="recipient",
            field=models.ForeignKey(
                on_delete=deletion.CASCADE, related_name="+",
                to="clubadm.Member"),
        ),
        migrations.AddField(
            model_name="mail",
            name="sender",
            field=models.ForeignKey(
                on_delete=deletion.CASCADE, related_name="+",
                to="clubadm.Member"),
        ),
        migrations.AlterUniqueTogether(
            name="member",
            unique_together=set([("user", "season")]),
        ),
    ]
