#-*- coding=utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


IMAGE_OS_TYPE = (
    (1, _("Windows")),
    (2, _("Linux")),
)

IMAGE_OS_TYPE_MAP = dict(IMAGE_OS_TYPE)


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(_("Image Name"), max_length=255)
    uuid = models.CharField(_("UUID"), max_length=255, help_text=_("Openstack Image UUID"))
    login_name = models.CharField(_("Login Name"), max_length=255)
    os_type = models.PositiveIntegerField(_("Image OS Type"), choices=IMAGE_OS_TYPE)
    disk_size = models.PositiveIntegerField(_("Free Disk"), default=30)

    data_center = models.ForeignKey('idc.DataCenter')
    user = models.ForeignKey('auth.User', null=True, blank=True, default=None)
    create_at = models.DateTimeField(_("Create Date"), auto_now_add=True)

    def __unicode__(self):
        return u"<Image ID:%s Name:%s %sGB>" % (self.id,
                    self.name, self.disk_size)

    @property
    def os_name(self):
        return IMAGE_OS_TYPE_MAP[self.os_type]

    @property
    def data_center_name(self):
        return self.data_center.name

    @property
    def owner_name(self):
        return self.user.username if self.user else ''

    class Meta:
        db_table = "image"
        verbose_name = _("Image")
        verbose_name_plural = _("Image")
