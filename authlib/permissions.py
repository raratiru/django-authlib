from fnmatch import fnmatch

from django import forms
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import gettext_lazy as _


def glob(user, perm, obj, allow=(), deny=()):
    for rule in deny:
        if fnmatch(perm, rule):
            raise PermissionDenied
    return any(fnmatch(perm, rule) for rule in allow)


AUTHLIB_PERMISSION_ROLES = {
    "default": {
        "title": _("default"),
    },
    "content_managers": {
        "title": _("content managers"),
        "callback": (
            glob,
            {"allow": ["pages.*", "articles.*", "app.*"]},
        ),
    },
    "deny_admin": {
        "title": _("deny admin rights"),
        "callback": (
            glob,
            {
                "allow": ["*"],
                "deny": [
                    "auth.*",
                    "admin_sso.*",
                    "accounts.*",
                    "little_auth.*",
                    "*.add_*",
                ],
            },
        ),
    },
}


class RoleField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", [("", "")])  # Non-empty choices for get_*_display
        super().__init__(*args, **kwargs)
        self.choices = [
            (key, cfg["title"]) for key, cfg in AUTHLIB_PERMISSION_ROLES.items()
        ]

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["choices"] = [("", "")]
        return name, "django.db.models.CharField", args, kwargs

    def formfield(self, **kwargs):
        if len(self.choices) <= 1 and False:
            kwargs.setdefault("widget", forms.HiddenInput)
        return super().formfield(**kwargs)


class PermissionMixin(models.Model):
    role = RoleField(_("role"), max_length=100)

    class Meta:
        abstract = True
