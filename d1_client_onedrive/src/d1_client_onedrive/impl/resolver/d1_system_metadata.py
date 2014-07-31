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
''':mod:`resolver.d1_system_metadata`
=====================================

:Synopsis:
 - Resolve DataONE System Metadata.
:Author:
  DataONE (Dahl)
'''

# Stdlib.
import logging
import os

# D1.

# App.
from d1_client_onedrive.impl import directory
from d1_client_onedrive.impl import onedrive_exceptions
from d1_client_onedrive.impl import resolver_base

log = logging.getLogger(__name__)

#log.setLevel(logging.DEBUG)


class Resolver(resolver_base.Resolver):
  def __init__(self, options):
    self._options = options
    self._object_tree = object_tree

  def get_attributes(self, object_tree, path):
    raise onedrive_exceptions.PathException('<not implemented>')

  def get_directory(self, path):
    raise onedrive_exceptions.PathException('<not implemented>')

    ##reading the system metadata
    #obj = self._get_system_metadata(pid)
    #xml = obj.toxml()
    #if offset + size > len(xml):
    #  size = len(xml) - offset
    #return xml[offset:offset + size]
    #
    ## describes...
    #dfname = urllib.unquote(parts[4]).decode('utf-8')
    #dpid = self._get_object_pid(dfname)
    #sysm = self._get_system_metadata(dpid)
    #if offset + size > sysm.size:
    #  size = sysm.size - offset
    #self._get(dpid)
    #return self._datacache[dpid][offset:offset + size]

    #  related = obj.getRelatedObjects()
    #  if len(related['describes']) > 0:
    #    res.append('describes')
    #  abstxt = self._getAbstract(pid)
    #  if len(abstxt) > 0:
    #    res.append('abstract.txt')
    #  return res

    #    relations = obj.getRelatedObjects()
    #    for rel in relations['describes']:
    #      fname = self._getObjectFileName(rel)
    #      res.append(encode_path_element(fname))
    #    return res

    #  if parts[3] == 'systemmetadata.xml':
    #    #self._logger.debug('getattr systemmetadata.xml')
    #    #get system metadata
    #    #obj = d1_client.d1client.DataONEObject(parts[3], cnbase_url=self._base_url)
    #    #sysm = obj.getSystemMetadata()
    #    sysm = self._getSystemMetadata(pid)
    #    ctime = time.mktime(sysm.dateUploaded.timetuple())
    #    mtime = time.mktime(sysm.dateSysMetadataModified.timetuple())
    #    xml = sysm.toxml()
    #    return dict(st_mode=(stat.S_IFREG | 0444), st_size=len(xml),
    #                                        st_ctime=ctime,
    #                                        st_mtime=mtime,
    #                                        st_atime=now, st_nlink=1)

    #  if mfid == pid:
    #    #get object
    #    #self._logger.debug('getattr object')
    #    sysm = self._getSystemMetadata(pid)
    #    ctime = time.mktime(sysm.dateUploaded.timetuple())
    #    mtime = time.mktime(sysm.dateSysMetadataModified.timetuple())
    #    return dict(st_mode=(stat.S_IFREG | 0444), st_size=sysm.size,
    #                                        st_ctime=ctime,
    #                                        st_mtime=mtime,
    #                                        st_atime=now, st_nlink=1)
    #  if parts[3] == 'describes':
    #    #get list of objects described by this entry
    #    #self._logger.debug('getattr describes')
    #    obj = self._getObject(pid)
    #    relations = obj.getRelatedObjects()
    #    st_nlink = len(relations['describes'])
    #    return dict(st_mode=(stat.S_IFDIR | 0755),
    #                st_ctime=now, st_mtime=now, st_atime=now, st_nlink=st_nlink)
    #
    #  if parts[3] == 'abstract.txt':
    #    #self._logger.debug('getattr abstract')
    #    abstxt = self._getAbstract(pid)
    #    return dict(st_mode=(stat.S_IFREG | 0444), st_size=len(abstxt),
    #                                        st_ctime=now,
    #                                        st_mtime=now,
    #                                        st_atime=now, st_nlink=1)

    #  #should only be describes/<identifier>
    #  fname = urllib.unquote(parts[4]).decode('utf-8')
    #  pid = self._getObjectPid(fname)
    #  if parts[3] == 'describes':
    #    #self._logger.debug('getattr describes/{0}'.format(pid))
    #    try:
    #      sysm = self._getSystemMetadata(pid)
    #      ctime = time.mktime(sysm.dateUploaded.timetuple())
    #      mtime = time.mktime(sysm.dateSysMetadataModified.timetuple())
    #      return dict(st_mode=(stat.S_IFREG | 0444), st_size=sysm.size,
    #                                          st_ctime=ctime,
    #                                          st_mtime=mtime,
    #                                          st_atime=now,
    #                                          st_nlink=1)
    #    except:
    #      raise OSError(errno.ENOENT, '')
    #raise OSError(errno.ENOENT, '')
