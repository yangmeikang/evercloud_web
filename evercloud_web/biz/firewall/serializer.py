#-*-coding-utf-8-*-
from django.contrib.auth.models import User

from rest_framework import serializers
from biz.idc.models import UserDataCenter

from biz.firewall.models import Firewall,FirewallRules


class FirewallSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, default=None)
    user_data_center = serializers.PrimaryKeyRelatedField(queryset=UserDataCenter.objects.all(), required=False, allow_null=True, default=None)
    create_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=False, allow_null=True)

    def validate_user(self, value):
        request = self.context.get('request', None)
        return request.user

    def validate_user_data_center(self, value):
        request = self.context.get('request', None)
        return UserDataCenter.objects.get(pk=request.session["UDC_ID"])

    class Meta:
        model = Firewall


class FirewallRulesSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                required=False, allow_null=True, default=None)
    user_data_center = serializers.PrimaryKeyRelatedField(
                        queryset=UserDataCenter.objects.all(),
                        required=False, allow_null=True, default=None)
    create_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M",
                                    required=False, allow_null=True)
    direction_desc = serializers.CharField(source="get_direction_display",
                                    read_only=True)

    def validate_user(self, value):
        request = self.context.get('request', None)
        return request.user

    def validate_user_data_center(self, value):
        request = self.context.get('request', None)
        return UserDataCenter.objects.get(pk=request.session["UDC_ID"])

    class Meta:
        model = FirewallRules

