from django.db.models import Manager, Model, DateTimeField, BooleanField
from django.http import Http404


class AppManager(Manager):
    def get_queryset(self):
        return super(AppManager, self).get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super(AppManager, self).get_queryset()

    def deleted_set(self):
        return super(AppManager, self).get_queryset().filter(is_deleted=True)

    def get_or_none(self, **kwargs):
        try:
            return self.get_queryset().get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def filter_or_none(self, **kwargs):
        try:
            return self.get_queryset().filter(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_or_404(self, **kwargs):
        try:
            return self.get_queryset().get(**kwargs)
        except self.model.DoesNotExist:
            raise Http404

    def filter_or_404(self, **kwargs):
        try:
            return self.get_queryset().filter(**kwargs)
        except self.model.DoesNotExist:
            raise Http404


class BaseModel(Model):
    created_at = DateTimeField(auto_now_add=True)  # Soft create
    updated_at = DateTimeField(auto_now=True)  # Soft update
    is_deleted = BooleanField(default=False)  # Soft delete

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.is_deleted = True
        self.save()

    objects = AppManager()

    class Meta:
        abstract = True
