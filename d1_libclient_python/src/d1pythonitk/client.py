'''Module d1pythonitk.d1client
===========================

This module implements DataOneClient which provides a client supporting basic 
interaction with the DataONE infrastructure.

:Created: 20100111
:Author: DataONE (vieglais, dahl)

:Dependencies:

  - python 2.6


'''

# Stdlib.
import logging
import httplib
import urllib
import urllib2
import urlparse
import sys
import os

try:
  import cjson as json
except:
  import json

# 3rd party.
try:
  import d1common.types.objectlist_serialization
  import d1common.types.objectlocationlist_serialization
  import d1common.types.systemmetadata
  import d1common.types.logrecords_serialization
  import d1common.types.nodelist_serialization
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write('Try: sudo easy_install pyxb\n')
  raise

# DataONE.
from d1common import exceptions
from d1common import mime_multipart
from d1pythonitk import const
from d1pythonitk import objectlistiterator

#===============================================================================


class HttpRequest(urllib2.Request):
  '''Overrides the default Request class to enable setting the HTTP method.
  '''

  def __init__(self, *args, **kwargs):
    ''':param: Passed on to urllib2.Request.__init__
    :return: (None)
    '''
    self._method = 'GET'
    if kwargs.has_key('method'):
      self._method = kwargs['method']
      del kwargs['method']
    urllib2.Request.__init__(self, *args, **kwargs)

  def get_method(self):
    '''Get HTTP method.
    :param: (None)
    :return: (string) HTTP method.
    '''
    return self._method

#===============================================================================


class RESTClient(object):
  '''Simple REST client that utilizes the base DataONE exceptions
  for error handling if possible.
  '''

  logger = logging.getLogger()

  def __init__(self, target=const.URL_DATAONE_ROOT, timeout=const.RESPONSE_TIMEOUT):
    ''':param: (string, float) DataONE root URL, HTTP timeout
    :return: (None)
    '''
    self.status = None
    self.responseInfo = None
    self._BASE_DETAIL_CODE = '10000'
    self.target = self._normalizeTarget(target)
    self.timeout = timeout

    #TODO: Need to define these detailCode values

    self.logger.debug_ = lambda *x: self.log(self.logger.debug, x)
    self.logger.warn_ = lambda *x: self.log(self.logger.warn, x)
    self.logger.err_ = lambda *x: self.log(self.logger.error, x)

  def log(self, d, x):
    '''Log a message with context.
    :param: (flo) log, (string) message
    :return: (None)
    '''
    d(
      'file({0}) func({1}) line({2}): {3}'.format(
        os.path.basename(sys._getframe(2).f_code.co_filename), sys._getframe(
          2).f_code.co_name, sys._getframe(2).f_lineno, x
      )
    )

  def exceptionCode(self, extra):
    '''Generate exception code
    :param: (string) extra message
    :return: (None)
    '''
    return "%s.%s" % (self._BASE_DETAIL_CODE, str(extra))

  def _normalizeTarget(self, target):
    '''Internal method to ensure target url is in suitable form before 
    adding paths.
    'param: (string) url
    :return: (string) url with ending slash
    '''

    if not target.endswith("/"):
      target += "/"
    return target

  @property
  def headers(self):
    '''Get dictionary of headers
    :return: (dict) headers
    '''

    return {'User-Agent': 'Test client', 'Accept': '*/*'}

  def loadError(self, response):
    '''Try and create a DataONE exception form the response. If successful, then
    the DataONE error will be raised, otherwise the error is encapsulated with a
    DataONE ServiceFailure exception and re-raised.
    
    :param: (response) Response from urllib2.urlopen
    :return: (exception) Should not return - always raises an exception.
    '''

    edata = response.read()
    exc = exceptions.DataOneExceptionFactory.createException(edata)
    if not exc is None:
      raise exc
    return False

  def sendRequest(self, url, method='GET', data=None, headers=None):
    '''Sends a HTTP request and returns the response as a file like object.
    
    Has the side effect of setting the status and responseInfo properties. 
    
    :param url: The target URL
    :type url: string
    :param method: The HTTP method to use.
    :type method: string
    :param data: Optional dictionary of data to pass on to urllib2.urlopen
    :type data: dictionary
    :param headers: Optional header information
    :type headers: dictionary
    '''

    if headers is None:
      headers = self.headers
    request = HttpRequest(url, data=data, headers=headers, method=method)

    self.logger.debug_('url({0}) headers({1}) method({2})'.format(url, headers, method))

    try:
      response = urllib2.urlopen(request, timeout=self.timeout)
      self.status = response.code
      self.responseInfo = response.info()
    except urllib2.HTTPError, e:
      self.logger.warn_('HTTPError({0})'.format(e))
      self.status = e.code
      self.responseInfo = e.info()
      if hasattr(e, 'read'):
        if self.loadError(e):
          return None
      raise (e)
#      if not self.loadError(e):
#        description = "HTTPError. Code=%s" % str(e.code)
#        traceInfo = {'body': e.read()}
#        raise exceptions.ServiceFailure('10000.0',description,traceInfo)
    except urllib2.URLError, e:
      self.logger.warn_('URLError({0})'.format(e))
      if hasattr(e, 'read'):
        if self.loadError(e):
          return None
      raise (e)
      #description = "URL Error. Reason=%s" % e.reason
      #raise exceptions.ServiceFailure('10000.1',description)
    return response

  def HEAD(self, url, headers=None):
    '''Issue a HTTP HEAD request.
    :param: (string) url, (dict) headers
    :return: (response)
    '''

    return self.sendRequest(url, headers=headers, method='HEAD')

  def GET(self, url, headers=None):
    '''Issue a HTTP GET request.
    :param: (string) url, (dict) headers
    :return: (response)
    '''

    return self.sendRequest(url, headers=headers, method='GET')

  def PUT(self, url, data, headers=None):
    '''Issue a HTTP PUT request.
    :param: (string) url, (string) data, (dict) headers
    :return: (response)
    '''

    if isinstance(data, dict):
      data = urllib.urlencode(data)
    return self.sendRequest(url, data=data, headers=headers, method='PUT')

  def POST(self, url, data, headers=None):
    '''Issue a HTTP POST request.
    :param: (string) url, (string) data, (dict) headers
    :return: (response)
    '''

    if isinstance(data, dict):
      data = urllib.urlencode(data)
    return self.sendRequest(url, data=data, headers=headers, method='POST')

  def DELETE(self, url, data=None, headers=None):
    '''Issue a HTTP DELETE request.
    :param: (string) url, (string) data, (dict) headers
    :return: (response)
    '''
    return self.sendRequest(url, data=data, headers=headers, method='DELETE')

#===============================================================================


class DataOneClient(object):
  '''Simple DataONE client.
  '''

  def __init__(
    self,
    target=const.URL_DATAONE_ROOT,
    userAgent=const.USER_AGENT,
    clientClass=RESTClient,
    timeout=const.RESPONSE_TIMEOUT,
  ):
    '''Initialize the test client.
    
    :param target: URL of the service to contact.
    :param UserAgent: The userAgent string being passed in the request headers
    :param clientClass: Class that will be used for HTTP connections.
    :return: (None)
    '''

    self.logger = clientClass.logger
    self.userAgent = userAgent
    self._BASE_DETAIL_CODE = '11000'
    #TODO: Need to define this detailCode base value
    self.client = clientClass(target, timeout)

  def exceptionCode(self, extra):
    '''Generate exception code.
    :param: (string) extra message
    :return: (string) exception code
    '''

    return "%s.%s" % (self._BASE_DETAIL_CODE, str(extra))

  @property
  def headers(self):
    '''Get headers.
    :param: (None)
    :return: (dict) headers
    '''
    res = {'User-Agent': self.userAgent, 'Accept': 'text/xml'}
    return res

  def getObjectUrl(self, id=None):
    '''Get the base URL to an object on target.
    :param: (None)
    :return: (string) url
    '''

    res = urlparse.urljoin(self.client.target, const.URL_OBJECT_PATH)
    if id is None:
      return res
    res = urlparse.urljoin(res, urllib.quote(id, ''))
    return res

  def getObjectListUrl(self):
    '''Get the full URL to the object collection on target.
    :param: (None)
    :return: (string) url
    '''

    return urlparse.urljoin(self.client.target, const.URL_OBJECT_LIST_PATH)

  def getMonitorUrl(self):
    '''Get the full URL to the object collection on target.
    :param: (None)
    :return: (string) url
    '''

    return urlparse.urljoin(self.client.target, const.URL_MONITOR_PATH)

  def getMetaUrl(self, id=None):
    '''Get the full URL to the SysMeta object on target.
    :param: (None)
    :return: (string) url
    '''

    res = urlparse.urljoin(self.client.target, const.URL_SYSMETA_PATH)
    if id is None:
      return res
    return urlparse.urljoin(res, urllib.quote(id, ''))

  def getAccessLogUrl(self):
    '''Get the full URL to the access log collection on target.
    :param: (None)
    :return: (string) url
    '''

    return urlparse.urljoin(self.client.target, const.URL_ACCESS_LOG_PATH)

  def getResolveUrl(self):
    '''Get the full URL to the resolve collection on target.
    :param: (None)
    :return: (string) url
    '''

    return urlparse.urljoin(self.client.target, const.URL_RESOLVE_PATH)

  def getNodeUrl(self):
    '''Get the full URL to the node collection on target.
    :param: (None)
    :return: (string) url
    '''

    return urlparse.urljoin(self.client.target, const.URL_NODE_PATH)

  def getSystemMetadataSchema(self, schemaUrl=const.SYSTEM_METADATA_SCHEMA_URL):
    '''Convenience function to retrieve the SysMeta schema.
    
    :param schemaUrl: The URL from which to load the schema from
    :type schemaUrl: string
    :return: (unicode) SysMeta schema
    '''

    response = self.client.GET(schemaUrl)
    return response

  def enumerateObjectFormats(self, object_formats={}):
    '''Get a list of object formats available on the target.
    :param: (dict) Dictionary to add discovered objects to
    :return: (object format, count) object formats
    '''

    object_list = objectlistiterator.ObjectListIterator(self)
    object_formats = {}
    for info in object_list:
      logging.debug("ID:%s | FMT: %s" % (info.identifier, info.objectFormat))
      try:
        object_formats[info.objectFormat] += 1
      except KeyError:
        object_formats[info.objectFormat] = 1
    return object_formats

  ## === DataONE API Methods ===
  def get(self, identifier, headers=None):
    '''Retrieve an object from DataONE.
    :param: (string) Identifier of object to retrieve.
    :return: (file) Open file stream.
    '''

    if len(identifier) == 0:
      self.logger.debug_("Invalid parameter(s)")

    url = self.getObjectUrl(id=identifier)
    self.logger.debug_("identifier({0}) url({1})".format(identifier, url))
    if headers is None:
      headers = self.headers
    response = self.client.GET(url, headers)
    return response

  def getSystemMetadataResponse(self, identifier, headers=None):
    '''Retrieve a SysMeta object from DataONE.
    :param: (string) Identifier of object for which to retrieve SysMeta.
    :return: (file, :class:d1sysmeta.SystemMetadata) Open file stream.
    '''

    if len(identifier) == 0:
      self.logger.debug_("Invalid parameter(s)")
    url = self.getMetaUrl(id=identifier)
    self.logger.debug_("identifier({0}) url({1})".format(identifier, url))
    if headers is None:
      headers = self.headers
    response = self.client.GET(url, headers)
    return response

  def getSystemMetadata(self, identifier, headers=None):
    '''Get de-serialized SystemMetadata object.
    :param: (string) Identifier of object for which to retrieve SysMeta
    :return: (class) De-serialized SystemMetadata object.
    '''

    response = self.getSystemMetadataResponse(identifier, headers)
    format = response.headers['content-type']
    return d1common.types.systemmetadata.CreateFromDocument(response.read(), format)

  def resolve(self, identifier, headers=None):
    '''Resolve an identifier into a ObjectLocationList.
    :param: (string) Identifier of the object to resolve.
    :return: :class:ObjectLocationList
    '''

    if len(identifier) == 0:
      self.logger.debug_("Invalid parameter(s)")

    url = urlparse.urljoin(self.getResolveUrl(), urllib.quote(identifier, ''))
    self.logger.debug_("identifier({0}) url({1})".format(identifier, url))
    if headers is None:
      headers = self.headers
    # Fetch.
    response = self.client.GET(url, headers)
    format = response.headers['content-type']
    deser = d1common.types.objectlocationlist_serialization.ObjectLocationList()
    return deser.deserialize(response.read(), format)

  def node(self, headers=None):
    '''Get Node registry.
    :param: (Node)
    :return: (class) :class:NodeList
    '''

    url = self.getNodeUrl()
    self.logger.debug_("url({0})".format(url))
    if headers is None:
      headers = self.headers
    # Fetch.
    response = self.client.GET(url, headers)
    format = response.headers['content-type']
    deser = d1common.types.nodelist_serialization.NodeList()
    return deser.deserialize(response.read(), format)

  def listObjects(
    self,
    startTime=None,
    endTime=None,
    objectFormat=None,
    start=0,
    count=const.MAX_LISTOBJECTS,
    requestFormat="text/xml",
    headers=None
  ):
    '''Perform the MN_replication.listObjects call.
    
    :param startTime:
    :param endTime:
    :param objectFormat:
    :param start:
    :param count:
    
    :return: (class) :class:ObjectList
    '''
    # Sanity.
    params = {}
    if start < 0:
      raise exceptions.InvalidRequest(10002, "'start' must be a positive integer")
    params['start'] = start
    try:
      if count < 0:
        raise ValueError
      if count > const.MAX_LISTOBJECTS:
        raise ValueError
    except ValueError:
      raise exceptions.InvalidRequest(
        10002,
        "'count' must be an integer between 1 and {0}".format(const.MAX_LISTOBJECTS)
      )
    else:
      params['count'] = count

    if endTime is not None and startTime is not None and startTime >= endTime:
      raise exceptions.InvalidRequest(10002, "startTime must be before endTime")

    # Date range.
    if startTime is not None:
      params['startTime'] = startTime.isoformat()
    if endTime is not None:
      params['endTime'] = endTime.isoformat()

    # Object format.
    if objectFormat is not None:
      params['objectFormat'] = objectFormat

    # Generate URL.
    url = "{0}?{1}".format(self.getObjectListUrl(), urllib.urlencode(params))
    self.logger.debug("%s: url=%s" % (__name__, url))

    if headers is None:
      headers = self.headers
    #TODO: Conflict between requestFormat and headers?
    headers['Accept'] = requestFormat

    # Fetch.
    self.logger.debug_("url({0}) headers({1})".format(url, headers))
    response = self.client.GET(url, headers)

    # Deserialize.
    format = response.headers['content-type']
    serializer = d1common.types.objectlist_serialization.ObjectList()
    # TODO: Remove buffering.
    return serializer.deserialize(response.read(), format)

  def getLogRecords(
    self,
    startTime=None,
    endTime=None,
    objectFormat=None,
    start=0,
    count=const.MAX_LISTOBJECTS
  ):
    '''Get log records from MN.
    
    :param startTime:
    :param endTime:
    :param objectFormat:
    :param start:
    :param count:
    
    :return: (class) :class:LogRecords
    '''

    params = {}

    if start < 0:
      raise exceptions.InvalidRequest(10002, "start must be a positive integer")
    params['start'] = start

    try:
      if count < 1:
        raise ValueError
      if count > const.MAX_LISTOBJECTS:
        raise ValueError
    except ValueError:
      raise exceptions.InvalidRequest(
        10002, "count must be an integer between 1 and {0}".format(const.MAX_LISTOBJECTS)
      )
    params['count'] = count

    if endTime is not None and startTime is not None and startTime >= endTime:
      raise exceptions.InvalidRequest(10002, "startTime must be before endTime")

    # Date range.
    if startTime is not None:
      params['startTime'] = startTime.isoformat()
    if endTime is not None:
      params['endTime'] = endTime.isoformat()

    url = self.getAccessLogUrl() + '?' + urllib.urlencode(params)

    headers = self.headers
    headers['Accept'] = 'text/xml'

    self.logger.debug_("url({0}) headers({1})".format(url, headers))

    # Fetch.
    response = self.client.GET(url, headers)
    format = response.headers['content-type']
    deser = d1common.types.logrecords_serialization.LogRecords()
    return deser.deserialize(response.read(), format)

  #def create(self, identifier, object_bytes, sysmeta_bytes):
  #  # Create MIME-multipart Mixed Media Type body.
  #  files = []
  #  files.append(('object', 'object', object_bytes))
  #  files.append(('systemmetadata', 'systemmetadata', sysmeta_bytes))
  #  content_type, mime_doc = mime_multipart.encode_multipart_formdata([], files)
  #  
  #  # Send REST POST call to register object.
  #
  #  headers = {
  #    'Content-Type': content_type,
  #    'Content-Length': str(len(mime_doc)),
  #  }
  #  
  #  crud_create_url = urlparse.urljoin(self.getObjectUrl(), urllib.quote(identifier, ''))
  #
  #  self.logger.debug_("url({0}) identifier({1}) headers({2})".format(crud_create_url, identifier, headers))
  #
  #  try:
  #    res = self.client.POST(crud_create_url, data=mime_doc, headers=headers)
  #    res = '\n'.join(res)
  #    if res != r'OK':
  #      raise Exception(res)
  #  except Exception as e:
  #    logging.error('REST call failed: {0}'.format(str(e)))
  #    raise

  def create(self, identifier, object_bytes, sysmeta_bytes):
    '''Create an object in DataONE.
    :param: (string) Identifier of object to create.
    :param: (flo or string) Object data.
    :param: (flo or string) SysMeta.
    :return: (None)
    '''

    # Parameter validation.
    if len(identifier) == 0:
      self.logger.debug_("Invalid parameter(s)")

    # Data to post.
    files = []
    files.append(('object', 'object', object_bytes))
    files.append(('systemmetadata', 'systemmetadata', sysmeta_bytes))

    # Send REST POST call to register object.

    crud_create_url = urlparse.urljoin(self.getObjectUrl(), urllib.quote(identifier, ''))
    self.logger.debug_('url({0}) identifier({1})'.format(crud_create_url, identifier))

    multipart = mime_multipart.multipart({}, [], files)
    try:
      status, reason, page = multipart.post(crud_create_url)
      if status != 200:
        raise Exception(page)
    except Exception as e:
      logging.error('REST call failed: {0}'.format(str(e)))
      raise
