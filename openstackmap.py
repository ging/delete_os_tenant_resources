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

import osclients
import cPickle as pickle
import sys
import os.path

persistence_dir = os.path.expanduser('~/persistence')


use_wrapper = True

class __D(dict):
    def __init__(self, d=dict()):
        self.__dict__ = self
        dict.__init__(self, d) 


def load(name):
    objects = pickle.load(open(persistence_dir + '/' + name + '.pickle', 'rb'))
    if use_wrapper:
       objects = list(__D(object) for object in objects)
    return objects
    
def get_and_save_keystone():
    global users, roles, tenants, roles_a 

    keystone = osclients.get_keystoneclientv3()
    with open(persistence_dir + '/roles.pickle', 'wb') as f:
        roles = list(role.to_dict() for role in keystone.roles.list())
        pickle.dump(roles, f, protocol=-1)

    with open(persistence_dir + '/users.pickle', 'wb') as f:
        users = list(user.to_dict() for user in keystone.users.list())
        pickle.dump(users, f, protocol=-1)

    with open(persistence_dir + '/tenants.pickle', 'wb') as f:
        tenants = list(tenant.to_dict() for tenant in keystone.projects.list())
        pickle.dump(tenants, f, protocol=-1)

    with open(persistence_dir + '/asignments.pickle', 'wb') as f:
        a = list(asig.to_dict() for asig in keystone.role_assignments.list())
        roles_a = a
        pickle.dump(roles_a, f, protocol=-1)

def load_keystone():
    global users_by_id, users_by_email, tenants_by_id, tenants_by_name
    global roles_by_user, roles_by_project
    global users, roles, tenants, roles_a 

    if not os.path.exists(persistence_dir + '/users.pickle'):
        get_and_save_keystone()
    else: 
        users = load('users')
        tenants = load('tenants')
        roles_a = load('asignments')
        roles = load('roles')

    users_by_email = dict()
    users_by_id = dict()
    for user in users:
        if 'name' in user:
            users_by_email[user['name']] = user
        users_by_id[user['id']] = user

    tenants_by_name = dict()
    tenants_by_id = dict()
    for tenant in tenants:
        tenants_by_id[tenant['id']] = tenant
        tenants_by_name[tenant['name']] = tenant

    rolesdict = dict((role['id'], role['name']) for role in roles)
    roles_by_user = dict()
    roles_by_project = dict()
    for roleasig in roles_a:
        userid = roleasig['user']['id']
        if 'project' in roleasig['scope']:
            projectid = roleasig['scope']['project']['id']
        else:
            projectid = str(roleasig['scope'])
        roleid = roleasig['role']['id']
        if userid not in roles_by_user:
            roles_by_user[userid] = list()
        if projectid not in roles_by_project:
            roles_by_project[projectid] = list()
        roles_by_user[userid].append((rolesdict[roleid], projectid))
        roles_by_project[projectid].append((rolesdict[roleid], userid))

def get_and_save_neutron():
    neutron = osclients.get_neutronclient()
    global networks, subnets, routers, floatingips 
    global security_groups, ports

    with open(persistence_dir + '/networks.pickle', 'wb') as f:
        networks = neutron.list_networks()['networks']
        pickle.dump(networks, f, protocol=-1)

    with open(persistence_dir + 'subnetworks.pickle', 'wb') as f:
        subnets = neutron.list_subnets()['subnets']
        pickle.dump(subnets, f, protocol=-1)

    with open(persistence_dir + 'routers.pickle', 'wb') as f:
        routers = neutron.list_routers()['routers']
        pickle.dump(routers, f, protocol=-1)

    with open(persistence_dir + 'floatingips.pickle', 'wb') as f:
        floatingips = neutron.list_floatingips()['floatingips']
        pickle.dump(floatingips, f, protocol=-1)

    with open(persistence_dir + 'securitygroups.pickle', 'wb') as f:
        security_groups = neutron.list_security_groups()['security_groups']
        pickle.dump(security_groups, f, protocol=-1)

    with open(persistence_dir + 'ports.pickle', 'wb') as f:
        ports = neutron.list_ports()['ports']
        pickle.dump(ports, f, protocol=-1)

def load_neutron():
    global networks, subnets, routers, floatingips 
    global security_groups, ports
    global security_groups_by_id

    if not os.path.exists(persistence_dir + '/networks.pickle'):    
        get_and_save_neutron()
        return

    networks = load('networks')
    subnets = load('subnetworks')
    routers = load('routers')
    floatingips = load('floatingips')
    security_groups = load('securitygroups')
    security_groups_by_id = dict( (sec['id'], sec) for sec in security_groups)
    ports = load('ports')


def get_and_save_nova():
    global vms

    nova = osclients.get_novaclient()

    with open(persistence_dir + '/vms.pickle', 'wb') as f:
        vm_list = nova.servers.list(search_opts={'all_tenants': 1})
        vms =list(vm.to_dict() for vm in vm_list)
        pickle.dump(vms, f, protocol=-1)

def load_nova():
    global vms
    global vms_by_id
    vms_by_id = dict()

    if not os.path.exists(persistence_dir + '/vms.pickle'):
        get_and_save_nova()
        return 

    #vms = pickle.load(open(persistence_dir + '/vms.pickle', 'rb'))
    vms = load('vms')
    vms_by_id = dict( (vm['id'], vm) for vm in vms)

def get_and_save_cinder():
    global volumes, backup_volumes, snapshot_cinder    

    cinder = osclients.get_cinderclient()

    with open(persistence_dir + '/volumes.pickle', 'wb') as f:
        volumes = list (volume.__dict__ for volume in cinder.volumes.list(search_opts={'all_tenants': 1}))
        pickle.dump(volumes, f, protocol=-1)

def load_cinder():
    global volumes
    global volumes_by_id

    if not os.path.exists(persistence_dir + '/volumes.pickle'):
        get_and_save_cinder()
    else:
        volumes = load('volumes')

    volumes_by_id = dict( (volume['id'], volume) for volume in volumes)

def get_and_save_glance():
    global images
    
    glance = osclients.get_glanceclient()
    with open(persistence_dir + '/images.pickle', 'wb') as f:
        images = list(image.to_dict() for image in  glance.images.findall())
        pickle.dump(images, f, protocol=-1)

def load_glance():
    global images, images_by_id
    if not os.path.exists(persistence_dir + '/images.pickle'):
        get_and_save_glance()
    else:
        images = load('images')
    images_by_id = dict( (image['id'], image) for image in images)

def load_all():
    load_neutron()
    load_nova()
    load_keystone()
    load_glance()
    load_cinder()

if not os.path.exists(persistence_dir):
    os.mkdir(persistence_dir)