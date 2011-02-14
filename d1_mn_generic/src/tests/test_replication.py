#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:mod:`test_replication`
=======================

:Synopsis:
  Test replication between two GMN instances.

  This test will only work until security is added to the DataONE
  infrastructure as the test works in part by simulating a CN. 
    
.. moduleauthor:: Roger Dahl
"""

import logging
import sys
import optparse
import urlparse
import urllib
import StringIO

# MN API.
try:
  #import d1_common.mime_multipart
  import d1_common.types.exceptions
  import d1_common.types.checksum_serialization
  import d1_common.types.objectlist_serialization
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write(
    'Try: svn co https://repository.dataone.org/software/cicore/trunk/api-common-python/src/d1_common\n'
  )
  raise
try:
  import d1_client
  import d1_client.xmlvalidator
  import d1_client.client
  import d1_client.systemmetadata
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write(
    'Try: svn co https://repository.dataone.org/software/cicore/trunk/itk/d1-python/src/d1_client\n'
  )
  raise

# 3rd party.
# Lxml
try:
  import lxml
  import lxml.objectify
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write('Try: sudo apt-get install python-lxml\n')
  raise


def log_setup():
  # Set up logging.
  # We output everything to both file and stdout.
  logging.getLogger('').setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(levelname)-8s %(message)s')
  console_logger = logging.StreamHandler(sys.stdout)
  console_logger.setFormatter(formatter)
  logging.getLogger('').addHandler(console_logger)


def baseurl_by_noderef(opts, node_ref):
  # Resolve dst_ref to URL.
  # Call to /cn/test_baseurl_by_noderef/<dst_node_ref>
  baseurl_by_noderef_url = urlparse.urljoin(opts.d1_root,
                                        'test_baseurl_by_noderef/{0}'\
                                        .format(urllib.quote(node_ref, '')))

  client_root = d1_client.client.DataOneClient(opts.d1_root)
  response = client_root.client.GET(baseurl_by_noderef_url)
  return response.read()


def replicate(opts, args):
  '''Replication. Requires fake CN.
  '''
  # The object we will replicate.
  #pid = 'hdl:10255/dryad.105/mets.xml'
  # Source and destination node references.
  dst_ref = args[0]
  src_ref = args[1]
  pid = args[2]

  logging.debug('src_ref({0}) dst_ref({1}) pid({2})'.format(src_ref, dst_ref, pid))

  # Create connections to src and dst.
  dst_base = baseurl_by_noderef(opts, dst_ref)
  client_dst = d1_client.client.DataOneClient(dst_base)
  src_base = baseurl_by_noderef(opts, src_ref)
  client_src = d1_client.client.DataOneClient(src_base)

  # For easy testing, delete the object on the destination node if it exists
  # there, so that we can test on the same object each time.
  try:
    pid_deleted = client_dst.delete(pid)
    assert (pid == pid_deleted.value())
  except d1_common.types.exceptions.NotFound:
    pass

  # Check that the object does not already exist on dst.
  #   We check for SyntaxError raised by the XML deserializer when it attempts
  #   to deserialize a DataONEException. The exception is caused by the body
  #   being empty since describe() uses a HEAD request.
  try:
    client_dst.describe(pid)
  except SyntaxError:
    pass
  else:
    logging.error('pid({0}): Object already exists on destination'.format(pid))
    exit()

  # Download the SysMeta doc from the source.
  sysmeta_obj = client_src.getSystemMetadata(pid)
  sysmeta_doc = sysmeta_obj.toxml()

  # Create the MMP document that is submitted to dst to request a replication.
  headers = {}
  headers[u'Content-type'] = 'multipart/form-data'
  headers[u'token'] = u'<dummy token>'
  files = []
  files.append(('sysmeta', 'sysmeta', sysmeta_doc))
  fields = []
  fields.append(('sourceNode', src_ref))
  multipart_obj = d1_common.mime_multipart.multipart(headers, fields, files)
  multipart_flo = StringIO.StringIO()
  for part in multipart_obj:
    multipart_flo.write(part)
  multipart_doc = multipart_flo.getvalue()
  #  return multipart_doc
  # Add replication task to the destination GMN work queue.
  client_t = d1_client.client.DataOneClient(dst_base)
  replicate_url = urlparse.urljoin(client_t.client.target, '/replicate')
  client_t.client.POST(replicate_url, multipart_doc, headers)

  #  # Poll for completed replication.
  #  replication_completed = False
  #  while not replication_completed:
  #    test_get_replication_status_xml = urlparse.urljoin(client_dst.client.target,
  #                                                    '/cn/test_get_replication_status_xml/{0}'.format(pid))
  #    status_xml_str = client_dst.client.GET(test_get_replication_status_xml).read()
  #    status_xml_obj = lxml.etree.fromstring(status_xml_str)
  #
  #    for replica in status_xml_obj.xpath('/replicas/replica'):
  #      if replica.xpath('replicaMemberNode')[0].text == src_node:
  #        if replica.xpath('replicationStatus')[0].text == 'completed':
  #          replication_completed = True
  #          break
  #
  #    if not replication_completed:
  #      time.sleep(1)
  #
  #  # Get checksum of the object on the destination server and compare it to
  #  # the checksum retrieved from the source server.
  #  dst_checksum_obj = client_dst.checksum(pid)
  #  dst_checksum = dst_checksum_obj.value()
  #  dst_algorithm = dst_checksum_obj.algorithm
  #  assertEqual(src_checksum, dst_checksum)
  #  assertEqual(src_algorithm, dst_algorithm)
  #  
  #  # Get the bytes of the object on the destination and compare them with the
  #  # bytes retrieved from the source.
  #  dst_obj_str = client_dst.get(pid).read()
  #  assertEqual(src_obj_str, dst_obj_str)


def main():
  log_setup()

  # Command line options.
  parser = optparse.OptionParser(
    'usage: %prog [options] <dst_gmn_ref> <src_gmn_ref> <pid>'
  )
  # General
  parser.add_option(
    '--d1-root',
    dest='d1_root',
    action='store',
    type='string',
    default='http://0.0.0.0:8000/cn/'
  ) # default=d1_common.const.URL_DATAONE_ROOT
  parser.add_option(
    '--verbose',
    dest='verbose',
    action='store_true',
    default=False,
    help='display more information'
  )
  (opts, args) = parser.parse_args()

  if not opts.verbose:
    logging.getLogger('').setLevel(logging.ERROR)

  if len(args) != 3:
    parser.print_help()
    exit()

  multipart_doc = replicate(opts, args)
#   # Add replication task to the destination GMN work queue.
#  client_t = d1_client.client.DataOneClient('http://127.0.0.1:8000')
#  replicate_url = urlparse.urljoin(client_t.client.target, '/replicate')
#  client_t.client.POST(replicate_url, multipart_doc, {})

if __name__ == '__main__':
  main()
