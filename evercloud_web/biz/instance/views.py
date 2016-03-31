#coding=utf-8

import re
import logging
import uuid
from djproxy.views import HttpProxy
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes)

from biz.volume.models import Volume
from biz.volume.serializer import VolumeSerializer
from biz.firewall.models import Firewall
from biz.firewall.serializer import FirewallSerializer

from biz.instance.models import Instance, Flavor
from biz.instance.serializer import InstanceSerializer, FlavorSerializer
from biz.instance.utils import instance_action
from biz.instance.settings import (INSTANCE_STATES_DICT, INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATE_APPLYING, MonitorInterval)
from biz.billing.models import Order
from biz.account.utils import check_quota
from biz.account.models import Operation
from biz.workflow.models import Workflow, FlowInstance
from biz.workflow.settings import ResourceType
from biz.network.models import Network

from biz.common.decorators import require_GET
from cloud.instance_task import (instance_create_task,
                                instance_get_console_log,
                                instance_get, instance_get_port)

LOG = logging.getLogger(__name__)
OPERATION_SUCCESS = 1
OPERATION_FAILED = 0


class InstanceList(generics.ListCreateAPIView):
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer

    def list(self, request):
        try:
            udc_id = request.session["UDC_ID"]
            queryset = self.get_queryset().filter(
                user=request.user, user_data_center__pk=udc_id)
            serializer = InstanceSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()


class InstanceDetail(generics.RetrieveAPIView):
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            if obj and obj.user == request.user:
                serializer = InstanceSerializer(obj)
                return Response(serializer.data)
            else:
                raise
        except Exception as e:
            LOG.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)


class FlavorList(generics.ListCreateAPIView):
    queryset = Flavor.objects.all()
    serializer_class = FlavorSerializer

    def list(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data)


class FlavorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Flavor.objects.all()
    serializer_class = FlavorSerializer


@api_view(["POST"])
def create_flavor(request):
    try:
        serializer = FlavorSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Flavor is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Flavor data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create flavor for unknown reason.')})


@api_view(["POST"])
def update_flavor(request):
    try:
        flavor = Flavor.objects.get(pk=request.data['id'])
        serializer = FlavorSerializer(instance=flavor, data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Flavor is updated successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Flavor data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to update flavor for unknown reason.')})


@api_view(["POST"])
def delete_flavors(request):
    ids = request.data.getlist('ids[]')
    Flavor.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Flavors have been deleted!')}, status=status.HTTP_201_CREATED)


@check_quota(["instance", "vcpu", "memory"])
@api_view(["POST"])
def instance_create_view(request):
    count = request.DATA.get("instance", u"1")
    try:
        count = int(count)
    except:
        count = 1

    pay_type = request.data['pay_type']
    pay_num = int(request.data['pay_num'])

    if count > settings.BATCH_INSTANCE:
        return Response({"OPERATION_STATUS": OPERATION_FAILED},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    network_id = request.DATA.get("network_id", u"0")
    try:
        network = Network.objects.get(pk=network_id)
    except Network.DoesNotExist:
        pass
    else:
        if not network.router:
            msg = _("Your selected network has not linked to any router.")
            return Response({"OPERATION_STATUS": OPERATION_FAILED,
                            "msg": msg}, status=status.HTTP_409_CONFLICT)

    has_error, msg = False, None
    for i in range(count):
        serializer = InstanceSerializer(data=request.data, context={"request": request}) 
        if serializer.is_valid():
            name = request.DATA.get("name", "Server")
            if i > 0:
                name = "%s-%04d" % (name, i)
            ins = serializer.save(name=name)

            Operation.log(ins, obj_name=ins.name, action="launch", result=1)
            workflow = Workflow.get_default(ResourceType.INSTANCE)

            if settings.SITE_CONFIG['WORKFLOW_ENABLED'] and workflow:
                ins.status = INSTANCE_STATE_APPLYING
                ins.save()

                FlowInstance.create(ins, request.user, workflow, request.DATA['password'])
                msg = _("Your application for instance \"%(instance_name)s\" is successful, "
                        "please waiting for approval result!") % {'instance_name': ins.name}
            else:
                instance_create_task.delay(ins, password=request.DATA["password"])
                Order.for_instance(ins, pay_type=pay_type, pay_num=pay_num)
                msg = _("Your instance is created, please wait for instance booting.")
        else:
            has_error = True
            break

    if has_error: 
        return Response({"OPERATION_STATUS": OPERATION_FAILED},
                        status=status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"OPERATION_STATUS": OPERATION_SUCCESS,
                          "msg": msg}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def instance_action_view(request, pk):
    instance_id, action = request.data['instance'], request.data['action']
    data = instance_action(request.user, instance_id, action)
    return Response(data)


@api_view(["GET"])
def instance_status_view(request):
    return Response(INSTANCE_STATES_DICT)


@api_view(["GET"])
def instance_search_view(request):
    instance_set = Instance.objects.filter(
        deleted=False, user=request.user, status=INSTANCE_STATE_RUNNING,
        user_data_center=request.session["UDC_ID"])
    serializer = InstanceSerializer(instance_set, many=True)
    return Response(serializer.data)

### TODO: remove below two API for qos


def qos_get_instance_detail(instance):
    instance_data = InstanceSerializer(instance).data

    try:
        server = instance_get(instance)
        instance_data['host'] = getattr(server, 'OS-EXT-SRV-ATTR:host', None)
        instance_data['instance_name'] = getattr(server,
                                'OS-EXT-SRV-ATTR:instance_name', None)
    except Exception as e:
        LOG.error("Obtain host fail,msg: %s" % e)
    try:
        ports = instance_get_port(instance)
        if ports:
            instance_data['port'] = ports[0].port_id
        else:
            instance_data['port'] = False
    except Exception as e:
        LOG.error("Obtain instance port fail,msg: %s" % e)

    try:
        from biz.floating.models import Floating
        floating = Floating.get_instance_ip(instance.id)
        if floating:
            instance_data["bandwidth"] = floating.bandwidth
        else:
            instance_data["bandwidth"] = settings.DEFAULT_BANDWIDTH
    except Exception as e:
        LOG.error("Obtain instance bandwidth fail,msg: %s" % e)

    return instance_data


@require_GET
@authentication_classes([])
@permission_classes([])
def instance_detail_view_via_uuid_or_ip(request, uuid_or_ip):
    instance_uuid = -1
    try:
        instance_uuid = uuid.UUID(uuid_or_ip) 
    except:
        pass

    try:
        if uuid_or_ip.count(".") == 3:
            from biz.floating.models import Floating
            floatings = Floating.objects.filter(ip=uuid_or_ip,
                                        deleted=False)
            if floatings.exists():
                if floatings[0].resource_type == "INSTANCE":
                    instance_uuid = Instance.objects.get(
                             pk=floatings[0].resource).uuid
    except:
        pass

    try:
        instance = Instance.objects.get(uuid=instance_uuid)
    except Instance.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    return Response(qos_get_instance_detail(instance))

### remove below two API for qos end


@api_view(["GET"])
def instance_detail_view(request, pk):
    tag = request.GET.get("tag", 'instance_detail')
    try:
        instance = Instance.objects.get(pk=pk, user=request.user)
    except Exception as e:
        LOG.error("Get instance error, msg:%s" % e)
        return Response({"OPERATION_STATUS": 0, "MSG": "Instance no exist"}, status=status.HTTP_200_OK)

    if "instance_detail" == tag:
        return _get_instance_detail(instance)
    elif 'instance_log' == tag:
        log_data = instance_get_console_log(instance)
        return Response(log_data)


def _get_instance_detail(instance):

    instance_data = InstanceSerializer(instance).data

    try:
        server = instance_get(instance)
        instance_data['host'] = getattr(server, 'OS-EXT-SRV-ATTR:host', None)
        instance_data['instance_name'] = getattr(server,
                                'OS-EXT-SRV-ATTR:instance_name', None)
        instance_data['fault'] = getattr(server, 'fault', None)

    except Exception as e:
        LOG.error("Obtain host fail,msg: %s" % e)

    try:
        firewall = Firewall.objects.get(pk=instance.firewall_group.id)
        firewall_data = FirewallSerializer(firewall).data
        instance_data['firewall'] = firewall_data
    except Exception as e:
        LOG.exception("Obtain firewall fail, msg:%s" % e)

    # 挂载的所有硬盘
    volume_set = Volume.objects.filter(instance=instance, deleted=False)
    volume_data = VolumeSerializer(volume_set, many=True).data
    instance_data['volume_list'] = volume_data

    return Response(instance_data)


@require_GET
def monitor_settings(request):
    monitor_config = settings.MONITOR_CONFIG.copy()
    monitor_config['intervals'] = MonitorInterval.\
        filter_options(monitor_config['intervals'])

    monitor_config.pop('base_url')

    return Response(monitor_config)


class MonitorProxy(HttpProxy):
    base_url = settings.MONITOR_CONFIG['base_url']

    forbidden_pattern = re.compile(r"elasticsearch/.kibana/visualization/")

    def proxy(self):
        url = self.kwargs.get('url', '')

        if self.forbidden_pattern.search(url):
            return HttpResponse('', status=status.HTTP_403_FORBIDDEN)

        return super(MonitorProxy, self).proxy()

monitor_proxy = login_required(csrf_exempt(MonitorProxy.as_view()))
