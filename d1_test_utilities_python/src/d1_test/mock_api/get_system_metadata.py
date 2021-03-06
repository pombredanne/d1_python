#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2016 DataONE
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
"""Mock:

CNRead.getSystemMetadata(session, pid) → SystemMetadata
https://releases.dataone.org/online/api-documentation-v2.0.1/apis/CN_APIs.html#CNRead.getSystemMetadata
MNRead.getSystemMetadata(session, pid) → SystemMetadata
https://releases.dataone.org/online/api-documentation-v2.0.1/apis/MN_APIs.html#MNRead.getSystemMetadata

A DataONEException can be triggered by adding a custom header named "trigger"
with the status code of the error to trigger, using vendorSpecific parameter.
E.g.:

client.getSystemMetadata(..., vendorSpecific={'trigger': '404'})
"""

# Stdlib
import re

import d1_common.const
import d1_common.type_conversions
import d1_common.url
import d1_test.mock_api.d1_exception
import d1_test.mock_api.util
import responses

# Config

N_TOTAL = 100
META_ENDPOINT_RX = r'v([123])/meta/(.*)'


def init(base_url):
  responses.add_callback(
    responses.GET,
    re.
    compile(r'^' + d1_common.url.joinPathElements(base_url, META_ENDPOINT_RX)),
    callback=_request_callback,
    content_type='',
  )


def _request_callback(request):
  # Return DataONEException if triggered
  exc_response_tup = d1_test.mock_api.d1_exception.trigger_by_header(request)
  if exc_response_tup:
    return exc_response_tup
  # Return NotFound
  pid, pyxb_bindings = _parse_meta_url(request.url)
  if pid.startswith('unknown_'):
    return d1_test.mock_api.d1_exception.trigger_by_status_code(request, 404)
  # Return regular response
  sysmeta_pyxb = d1_test.mock_api.util.generate_sysmeta(pyxb_bindings, pid)[1]
  header_dict = {
    'Content-Type': d1_common.const.CONTENT_TYPE_XML,
  }
  return 200, header_dict, sysmeta_pyxb.toxml('utf8')


def _parse_meta_url(url):
  version_tag, endpoint_str, param_list, query_dict, pyxb_bindings = (
    d1_test.mock_api.util.parse_rest_url(url)
  )
  assert endpoint_str == 'meta'
  assert len(
    param_list
  ) == 1, 'getSystemMetadata() accepts a single parameter, the PID'
  return param_list[0], pyxb_bindings
