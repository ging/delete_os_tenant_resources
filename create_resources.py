#!/usr/bin/env python
# -- encoding: utf-8 --
#
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-Core project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es
#

author = 'chema'

import time
import pycurl
import os

from osclients import OpenStackClients

image_name = 'debian7'

i_url = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img'
img_name = 'cirros0.3.4.img'
i_url2 = 'http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img'
img_name2 = 'cirros0.3.3.img'


class ResourcePopulator(object):
    """This class create resources to test that all of them are deleted by
    the code.

    It creates:
    *a volume
    *a private image
    *a router
    *a network and subnetwork
    *an interface in the router
    *an IP
    *a security group
    *a keypair
    *a VM
    *an association of a floating ip with the VM
    *a snapshot of the volume
    """

    def __init__(self):
        """constructor"""
        osclients = OpenStackClients()
        neutron = osclients.get_neutronclient()
        cinder = osclients.get_cinderclient()
        glance = osclients.get_glanceclient()
        nova = osclients.get_novaclient()

        print 'Creating a volume'
        volume = cinder.volumes.create(name='cindervolume', size=1)

        external_net = None
        for net in neutron.list_networks()['networks']:
            if net['router:external']:
                external_net = net['id']
                break

        properties = {'key1': 'value1'}

        print 'Creating a private image'
        image = glance.images.create(
            container_format='bare', name='testimage1', disk_format='qcow2',
            data='aaaaa', properties=properties, is_public=False)

        download_images()

        print 'Creating a shared image'
        cirrosfile = open(img_name)
        image_shared1 = glance.images.create(
            container_format='bare', name='testimage2', disk_format='qcow2',
            data=cirrosfile, properties={'key2': 'value2'}, is_public=True)

        print 'Creating another shared image'
        cirrosfile2 = open(img_name2)
        image_shared2 = glance.images.create(
            container_format='bare', name='testimage3', disk_format='qcow2',
            data=cirrosfile2, properties={'key3': 'value3'}, is_public=True)

        print 'Creating a keypair'
        keypair = nova.keypairs.create(name='testpublickey')

        print 'Allocating a new security group'
        secgroup = nova.security_groups.create('testsecgroup',
                                               'a security group for testing')

        print 'Reserving a flotaing ip'
        floatingip = nova.floating_ips.create(pool=external_net)

        print 'Creating a router'
        router = neutron.create_router(
            {'router': {'name': 'testrouter', 'admin_state_up': True}}
        )['router']

        print 'Creating a network'
        n = neutron.create_network(
            {'network': {'name': 'testnetwork', 'admin_state_up': True, }})
        network = n['network']

        print 'Creating a subnet'
        subnet = neutron.create_subnet(
            {'subnet': {'name': 'testsubnet', 'network_id': network['id'],
                        'ip_version': 4, 'cidr': '192.168.1.0/24',
                        'dns_nameservers': ['8.8.8.8']}})['subnet']

        """
        Only admin users can create shared networks.

        network2 = neutron.create_network(
            {'network': {'name': 'testnetwork_shared', 'admin_state_up': True,
                         'shared': True}})['network']

        subnet2 = neutron.create_subnet(
            {'subnet': {'name': 'testsubnet_shared',
                        'network_id': network2['id'],
                        'ip_version': 4, 'cidr': '192.168.2.0/24',
                        'dns_nameservers': ['8.8.8.8']}})['subnet']

        """

        print 'Adding interface and gateway to router'
        neutron.add_interface_router(router['id'], {'subnet_id': subnet['id']})
        neutron.add_gateway_router(router['id'], {'network_id': external_net})

        # The volume must be available before creating the snapshot.
        time.sleep(3)

        print 'Creating a volume snapshot'
        snapshot = cinder.volume_snapshots.create(volume.id)

        # image_id = glance.images.find(name=image_name)
        image_id = image_shared1.id
        tiny = nova.flavors.find(name='m1.tiny')
        small = nova.flavors.find(name='m1.small')
        nic = {'net-id': network['id']}

        print 'Creating a VM'
        server = nova.servers.create(
            'vm_testdelete', flavor=tiny, image=image_id,
            key_name='testpublickey', security_groups=['default'], nics=[nic])
        # , files=files, config_drive=True)
        time.sleep(2)
        server.add_floating_ip(floatingip.ip)

        osclients2 = OpenStackClients()
        osclients2.set_credential('testdelete2', os.environ['PASSWORD_USER2'],
                                  'testdelete2')
        nova = osclients2.get_novaclient()
        neutron = osclients2.get_neutronclient()

        net2 = None
        for net in neutron.list_networks()['networks']:
            if not net['router:external']:
                net2 = net['id']
                break

        nics = [{'net-id': net2}]
        print 'Creating a second VM, with a different user'
        server2 = nova.servers.create(
            'vm_testdelete2', flavor=tiny, image=image_shared2.id, nics=nics)


def download_images():
    """auxiliary function to download Cirros images if they are not already
    download.
    """
    if not os.path.exists(img_name):
        print 'Downloading ' + img_name
        c = pycurl.Curl()
        c.setopt(pycurl.URL, i_url)
        c.setopt(pycurl.WRITEDATA, open(img_name, 'w'))
        c.perform()
    if not os.path.exists(img_name2):
        print 'Downloading ' + img_name2
        c = pycurl.Curl()
        c.setopt(pycurl.URL, i_url2)
        c.setopt(pycurl.WRITEDATA, open(img_name2, 'w'))
        c.perform()


resources = ResourcePopulator()
