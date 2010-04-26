'''Utility for validating XML schema.  Included here as a separate utility
as it is not required for core functionality of the DataONE toolkit but
can be quite useful for, well, validation purposes.

This all seems a bit excessive, and likely there's a simpler way to do this
without a custom resolver, but well, it's not obvious from the docs.
'''

import logging
from lxml import etree
try:
  from cStringIO import StringIO
except:
  from StringIO import StringIO

from d1pythonitk.client import RESTClient

#===============================================================================


class SchemaResolver(etree.Resolver):
  xsd_cache = {}
  '''Custom resolver that supports network retrieval of the schema and its 
  imported pieces.
  '''

  def resolve(self, url, id, context):
    '''Implements lxml Resolver.resolve
    '''
    logging.debug("resolve url = %s" % url)
    return self.resolve_filename(url, context)

  def resolve_filename(self, url, context):
    '''Load the target from the specified URL.
    '''
    logging.debug("resolve_filename url = %s" % url)

    # Get schema from cache or download it if necessary.
    if url in self.xsd_cache.keys():
      logging.debug('Retrieving XSD from cache: {0}'.format(url))
      xsd = self.xsd_cache[url]
    else:
      logging.debug('Downloading and caching XSD: {0}'.format(url))
      cli = RESTClient()
      fstream = cli.GET(url)
      xsd = fstream.read()
      # Cache the schema.
      self.xsd_cache[url] = xsd

    return self.resolve_string(xsd, context, base_url=url)

#===============================================================================


def validate(xmlDocument, schemaUrl):
  ''' Validate the supplied XML document text against a schema URL

  :param xmlDocument: xml text
  :type xmlDocument: basestring
  :param schemaUrl: URL pointing to the schema document to validate against
  :type schemaUrl: basestring
  '''
  resolver = SchemaResolver()
  xsdParser = etree.XMLParser()
  xsdParser.resolvers.add(resolver)
  schemaDoc = etree.parse(schemaUrl, xsdParser)
  xmlSchema = etree.XMLSchema(schemaDoc)

  sourceFile = StringIO(xmlDocument)
  xmlParser = etree.XMLParser(schema=xmlSchema)
  parsed = etree.parse(sourceFile, xmlParser)
