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

from user_resources import UserResources
from os import environ as env

# Ensure we are not using other credentials
if 'OS_USERNAME' in env:
    del env['OS_USERNAME']
if 'OS_PASSWORD' in env:
    del env['OS_PASSWORD']
if 'OS_TENANT_NAME' in env:
    del env['OS_TENANT_NAME']
if 'OS_TENANT_ID' in env:
    del env['OS_TENANT_ID']


users_credentials = open('users_credentials.txt')

for line in users_credentials.readlines():
    (user, password, tenant_id) = line.strip().split(',')
    print 'Stopping active VMs of user ' + user
    user_resources = UserResources(user, password, tenant_id=tenant_id)
    user_resources.stop_tenant_vms()
    print 'Unshare public images of user ' + user
    user_resources.unshare_images()
