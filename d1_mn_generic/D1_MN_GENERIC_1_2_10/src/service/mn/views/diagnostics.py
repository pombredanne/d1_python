#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2012 DataONE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

''':mod:`views.diagnostics`
===========================

:Synopsis:
  REST call handlers for GMN diagnostic APIs.
  These are used in various diagnostics, debugging and testing scenarios.
  Access is unrestricted in debug mode. Disabled in production.
:Author: DataONE (Dahl)
'''
# Stdlib.
import cgi
import csv
import os
import pprint
import time
import urlparse

# Django.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q

# D1.
import d1_common.const
import d1_common.date_time
import d1_common.types.exceptions
import d1_common.types.generated.dataoneTypes as dataoneTypes

# App.
import mn.view_asserts
import mn.auth
import mn.db_filter
import mn.event_log
import mn.models
import mn.node_registry
import mn.psycopg_adapter
import mn.restrict_to_verb
import mn.sysmeta_store
import mn.urls
import mn.util
import mn.view_shared
import service.settings


# ------------------------------------------------------------------------------
# Diagnostics portal.
# ------------------------------------------------------------------------------

@mn.restrict_to_verb.get
def diagnostics(request):
  if 'clear_db' in request.GET:
    _delete_all_objects()
    _clear_replication_queue()
    _delete_subjects_and_permissions()
  return render_to_response('test.html', d1_common.const.CONTENT_TYPE_XHTML)

# ------------------------------------------------------------------------------
# Replication.
# ------------------------------------------------------------------------------

@mn.restrict_to_verb.get
def get_replication_queue(request):
  q = mn.models.ReplicationQueue.objects.all()
  if 'excludecompleted' in request.GET:
    q = mn.models.ReplicationQueue.objects.filter(
      ~Q(status__status='completed'))
  return render_to_response('replicate_get_queue.xml',
    {'replication_queue': q },
    content_type=d1_common.const.CONTENT_TYPE_XML)


@mn.restrict_to_verb.get
def clear_replication_queue(request):
  _clear_replication_queue()
  return mn.view_shared.http_response_with_boolean_true_type()


def _clear_replication_queue():
  mn.models.ReplicationQueue.objects.all().delete()

@mn.restrict_to_verb.post
def post_replicate(request, pid):
  '''MNReplication.replicate(session, sysmeta, sourceNode) → boolean
  '''
  mn.view_asserts.post_has_mime_parts(request, (('field', 'sourceNode'),
                                      ('file', 'sysmeta')))
  sysmeta_xml = request.FILES['sysmeta'].read().decode('utf-8')
  sysmeta = mn.view_shared.deserialize_system_metadata(sysmeta_xml)
  # _assert_request_complies_with_replication_policy(sysmeta)
  mn.view_asserts.pid_does_not_exist(sysmeta.identifier.value())
  mn.view_asserts.pid_has_not_been_accepted_for_replication(sysmeta.identifier.value())
  _create_replication_work_item(request, sysmeta)
  return mn.view_shared.http_response_with_boolean_true_type()

def _create_replication_work_item(request, sysmeta):
  replication_item = mn.models.ReplicationQueue()
  replication_item.set_status('new')
  replication_item.set_source_node(request.POST['sourceNode'])
  replication_item.pid = sysmeta.identifier.value()
  replication_item.save()

# ------------------------------------------------------------------------------
# Access Policy.
# ------------------------------------------------------------------------------

@mn.restrict_to_verb.get
def set_access_policy(request, pid):
  mn.view_asserts.object_exists(pid)
  mn.view_asserts.post_has_mime_parts(request, (('file', 'access_policy'),))
  access_policy_xml = request.FILES['access_policy'].read()
  access_policy = dataoneTypes.CreateFromDocument(access_policy_xml)
  mn.auth.set_access_policy(pid, access_policy)
  return mn.view_shared.http_response_with_boolean_true_type()


@mn.restrict_to_verb.get
def delete_all_access_policies(request):
  # The deletes are cascaded so all subjects are also deleted.
  mn.models.Permission.objects.all().delete()
  return mn.view_shared.http_response_with_boolean_true_type()

@mn.restrict_to_verb.get
def get_access_policy(request, pid):
  mn.view_asserts.object_exists(pid)
  mn.event_log.read(pid, request)
  sciobj = mn.models.ScienceObject.objects.get(pid=pid)
  sysmeta = mn.sysmeta_store.sysmeta(pid,sciobj.serial_version,read_only=True)
  return HttpResponse(sysmeta.sysmeta_pyxb.accessPolicy.toxml(), d1_common.const.CONTENT_TYPE_XML)

# ------------------------------------------------------------------------------
# Authentication.
# ------------------------------------------------------------------------------

@mn.restrict_to_verb.get
def echo_session(request):
  return render_to_response('echo_session.xhtml',
                            {'subjects': sorted(request.subjects) },
                            content_type=d1_common.const.CONTENT_TYPE_XHTML)


@mn.restrict_to_verb.get
def trusted_subjects(request):
  return render_to_response('trusted_subjects.xhtml',
    {'subjects': sorted(mn.node_registry.get_cn_subjects() |
                        service.settings.DATAONE_TRUSTED_SUBJECTS) },
    content_type=d1_common.const.CONTENT_TYPE_XHTML)

# ------------------------------------------------------------------------------
# Misc.
# ------------------------------------------------------------------------------

def create(request, pid):
  '''Version of create() that performs no locking, testing or validation.
  Used for inserting test objects.'''
  sysmeta_xml = request.FILES['sysmeta'].read().decode('utf-8')
  sysmeta = mn.view_shared.deserialize_system_metadata(sysmeta_xml)
  mn.view_shared.create(request, pid, sysmeta)
  return mn.view_shared.http_response_with_boolean_true_type()


@mn.restrict_to_verb.get
def slash(request, p1, p2, p3):
  '''Test that GMN correctly handles three arguments separated by slashes'''
  return render_to_response('test_slash.html', {'p1': p1, 'p2': p2, 'p3': p3})


@mn.restrict_to_verb.get
def exception(request, exception_type):
  '''Test that GMN correctly catches and serializes exceptions raised by views'''
  if exception_type == 'python':
    raise Exception("Test Python Exception")
  elif exception_type == 'dataone':
    raise d1_common.types.exceptions.InvalidRequest(0, 'Test DataONE Exception')

  return mn.view_shared.http_response_with_boolean_true_type()


@mn.restrict_to_verb.get
def echo_request_object(request):
  pp = pprint.PrettyPrinter(indent=2)
  return HttpResponse('<pre>{0}</pre>'.format(cgi.escape(pp.pformat(request))))


@mn.restrict_to_verb.get
def permissions_for_object(request, pid):
  mn.view_asserts.object_exists(pid)
  subjects = []
  permissions = mn.models.Permission.objects.filter(object__pid = pid)
  for permission in permissions:
    action = mn.auth.level_action_map[permission.level]
    subjects.append((permission.subject.subject , action))
  return render_to_response('permissions_for_object.xhtml', locals(),
                          content_type=d1_common.const.CONTENT_TYPE_XHTML)

@mn.restrict_to_verb.get
def get_setting(request, setting):
  '''Get a value from settings.py or settings_site.py'''
  return HttpResponse(getattr(service.settings, setting, '<UNKNOWN SETTING>'),
                      d1_common.const.CONTENT_TYPE_TEXT)

#@mn.restrict_to_verb.post
def echo_raw_post_data(request):
  return HttpResponse(request.raw_post_data)


@mn.restrict_to_verb.get
def delete_all_objects(request):
  _delete_all_objects()
  delete_event_log(request)
  return mn.view_shared.http_response_with_boolean_true_type()


def _delete_all_objects():
  for object_ in mn.models.ScienceObject.objects.all():
    _delete_object(object_.pid)


def _delete_subjects_and_permissions():
  mn.models.Permission.objects.all().delete()
  mn.models.PermissionSubject.objects.all().delete()


@mn.restrict_to_verb.get
def delete_single_object(request, pid):
  '''Note: The semantics for this method are different than for the production
  method that deletes an object. This method removes all traces that the object
  ever existed.
  '''
  _delete_object(pid)
  return mn.view_shared.http_response_with_boolean_true_type()


def _delete_object(pid):
  #mn.view_asserts.object_exists(pid)
  sciobj = mn.models.ScienceObject.objects.get(pid=pid)
  # If the object is wrapped, only delete the reference. If it's managed, delete
  # both the object and the reference.
  url_split = urlparse.urlparse(sciobj.url)
  if url_split.scheme == 'file':
    sciobj_path = mn.util.store_path(service.settings.OBJECT_STORE_PATH, pid)
    try:
      os.unlink(sciobj_path)
    except EnvironmentError:
      pass
  # At this point, the object was either managed and successfully deleted or
  # wrapped and ignored. The SysMeta object is left orphaned in the filesystem
  # to be cleaned by an asynchronous process later. If the same object that
  # was just deleted is recreated, the old SysMeta object will be overwritten
  # instead of being cleaned up by the async process.
  #
  # Delete the DB entry.
  #
  # By default, Django's ForeignKey emulates the SQL constraint ON DELETE
  # CASCADE. In other words, any objects with foreign keys pointing at the
  # objects to be deleted will be deleted along with them.
  #
  # TODO: This causes associated permissions to be deleted, but any subjects
  # that are no longer needed are not deleted. The orphaned subjects should
  # not cause any issues and will be reused if they are needed again.
  sciobj.delete()


# ------------------------------------------------------------------------------
# Event Log.
# ------------------------------------------------------------------------------

def delete_event_log(request):
  mn.models.EventLog.objects.all().delete()
  mn.models.EventLogIPAddress.objects.all().delete()
  mn.models.EventLogEvent.objects.all().delete()
  return mn.view_shared.http_response_with_boolean_true_type()


@mn.restrict_to_verb.post
def inject_fictional_event_log(request):
  mn.view_asserts.post_has_mime_parts(request, (('file', 'csv'),))

  # Create event log entries.
  csv_reader = csv.reader(request.FILES['csv'])

  for row in csv_reader:
    pid = row[0]
    event = row[1]
    ip_address = row[2]
    user_agent = row[3]
    subject = row[4]
    timestamp = d1_common.date_time.from_iso8601((row[5]))
    #member_node = row[6]

    # Create fake request object.
    request.META = {
      'REMOTE_ADDR': ip_address,
      'HTTP_USER_AGENT': user_agent,
      'REMOTE_ADDR': subject,
      'SERVER_NAME': 'dataone.org',
      'SERVER_PORT': '80',
    }

    mn.event_log._log(pid, request,
                      event, d1_common.date_time.strip_timezone(timestamp))

  return mn.view_shared.http_response_with_boolean_true_type()
