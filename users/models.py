from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from fcm_django.models import FCMDevice


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Please, type phone')

        user = self.model(
            username=username,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        user = self.create_user(
            username=username,
            password=password,
            **extra_fields
        )

        if extra_fields.get('is_staff') is not True:
            raise ValueError('is_staff=True required for Superuser')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('is_superuser=True required for Superuser')

        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    # not Delete! (не трогать)
    first_name = models.CharField(
        max_length=100,
        verbose_name='First name',
        null=True,
        blank=True
    )
    # not Delete! (не трогать)
    last_name = models.CharField(
        max_length=100,
        verbose_name='Last name',
        null=True,
        blank=True
    )
    username = models.CharField(
        max_length=256,
        verbose_name='Nickname',
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=256,
        verbose_name='Phone number',
        unique=True,
        null=True,
        blank=True
    )
    time_zone = models.CharField(
        max_length=256,
        verbose_name='Time zone',
        null=True,
        blank=True
    )
    avatar = models.ImageField(
        verbose_name='Avatar',
        upload_to="users/avatars/",
        null=True,
        blank=True
    )
    in_calendaria = models.BooleanField(
        default=False,
        verbose_name='Active?',
        help_text='Status (default "No")',
    )
    # Дата создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        null=True,
    )
    status = models.CharField(
        max_length=800,
        verbose_name='Text status',
        null=True,
        blank=True
    )
    status_change_at = models.DateTimeField(
        verbose_name='Status change date',
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
        null=True,
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name='Online?',
        help_text='Status (default "No")',
    )
    last_online = models.DateTimeField(
        verbose_name='Last online',
        null=True,
        blank=True
    )
    # Django Additional (не трогать)
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Is staff?',
        help_text='Only for admin panel',
    )  # права к админ-панели
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is active?',
        help_text='Status (default "Yes")',
    )  # активный аккаунт

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]
    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.phone


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='User who owns the contact',
        on_delete=models.CASCADE,
    )
    label = models.CharField(
        verbose_name='Label',
        max_length=200,
        null=True,
        blank=True
    )
    type = models.CharField(
        max_length=100,
        verbose_name='Type',
    )
    phone = models.CharField(
        max_length=100,
        verbose_name='Phone number',
    )
    in_calendaria = models.BooleanField(
        default=False,
        verbose_name='Active?',
        help_text='Status (default "No")',
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Deleted?',
        help_text='Status (default "No")',
    )

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'

    def __str__(self):
        return self.label


class Settings(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='User who owns the settings',
        on_delete=models.CASCADE,
    )
    theme = models.CharField(
        verbose_name='Theme',
        max_length=200,
        default='default',
    )

    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return self.user.id


class Privacy(models.Model):
    PRIVACY_OPTIONS = [
        ('No One', 'No One'),
        ('My Contacts', 'My Contacts'),
        ('All', 'All')
    ]
    user = models.ForeignKey(
        User,
        verbose_name='User who owns the privacy settings',
        on_delete=models.CASCADE,
    )
    last_actions = models.CharField(
        verbose_name='Who can see my last actions',
        choices=PRIVACY_OPTIONS,
        max_length=15,
        default='All'
    )
    profile_image = models.CharField(
        verbose_name='Who can see my profile image',
        choices=PRIVACY_OPTIONS,
        max_length=15,
        default='All'
    )
    group_chat_invite = models.CharField(
        verbose_name='Who can invite me to group chats',
        choices=PRIVACY_OPTIONS,
        max_length=15,
        default='All'
    )
    event_invite = models.CharField(
        verbose_name='Who can invite me to events',
        choices=PRIVACY_OPTIONS,
        max_length=15,
        default='All'
    )
    my_events = models.CharField(
        verbose_name='Who can see my events',
        choices=PRIVACY_OPTIONS,
        max_length=15,
        default='All'
    )

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'

    def __str__(self):
        return self.user.id


class UserRelations(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='User who owns the relation',
        on_delete=models.CASCADE,
    )
    related_user = models.ForeignKey(
        User,
        verbose_name='Related user',
        on_delete=models.CASCADE,
        related_name='relation'
    )
    blocked = models.BooleanField(
        default=False,
        verbose_name='Blocked?',
        help_text='Статус (по умолчанию "Нет")',
    )
    muted = models.BooleanField(
        default=False,
        verbose_name='Muted?',
        help_text='Статус (по умолчанию "Нет")',
    )
    autosave_media = models.BooleanField(
        default=True,
        verbose_name='Autosave media?',
        help_text='Статус (по умолчанию "Да")',
    )
    blocked_desc = models.CharField(
        max_length=100,
        verbose_name='Blocked description',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Relation'
        verbose_name_plural = 'Relations'

    def __str__(self):
        return self.user.id
