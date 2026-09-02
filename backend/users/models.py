from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):

    username = models.CharField(unique=True, max_length=150)

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        error_messages={
            "unique": "Пользователь с таким email уже существует.",
        },
        verbose_name="Электронная почта",
        max_length=254
    )

    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name="Имя",
    )

    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name="Фамилия",
    )

    avatar = models.ImageField(
        upload_to="avatar/images/",
        null=True,
        blank=True,
        default=None,
        verbose_name="Фотография",
        help_text="Фотография пользователя.",
    )

    def clean(self):
        super().clean()
        if not self.email:
            raise ValidationError({"email": "Email обязателен для заполнения"})
        if not self.first_name:
            raise ValidationError({"first_name": "Имя обязательно для заполнения"})
        if not self.last_name:
            raise ValidationError({"last_name": "Фамилия обязательна для заполнения"})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name="following",
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        help_text="Пользователь, который подписывается",
    )
    following = models.ForeignKey(
        CustomUser,
        related_name="followers",
        verbose_name="Автор",
        on_delete=models.CASCADE,
        help_text="Пользователь, на которого подписываются",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = (
            "user",
            "following",
        )
        constraints = [
            # Запрет подписки на самого себя
            models.CheckConstraint(
                check=~models.Q(user=models.F("following")),
                name="prevent_self_follow",
            )
        ]

    def __str__(self):
        return f"{self.user.username} подписан на {self.following.username}"
