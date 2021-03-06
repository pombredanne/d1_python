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
"""
Module d1_instance_generator.tests.test_systemmetadata
======================================================

:Synopsis: Unit tests for system metadata generator.
:Created: 2011-12-05
:Author: DataONE (Dahl)
"""

# Stdlib
import logging
import unittest
import StringIO

# D1
import d1_common.checksum
import d1_common.types.generated.dataoneTypes_v1 as dataoneTypes_v1
import d1_common.const
import d1_common.test_case_with_url_compare
import d1_common.types.exceptions

# App
import d1_test.instance_generator.checksum as checksum

#===============================================================================


class TestChecksum(d1_common.test_case_with_url_compare.TestCaseWithURLCompare):
  def setUp(self):
    pass

  def test_010(self):
    """get_checksum_calculator_by_dataone_designator() returns a checksum calculator"""
    calculator = checksum.get_checksum_calculator_by_dataone_designator('SHA-1')
    calculator.update('test')
    self.assertTrue(calculator.hexdigest())

  def test_011(self):
    """get_checksum_calculator_by_dataone_designator() raises on invalid algorithm"""
    self.assertRaises(
      Exception, checksum.get_checksum_calculator_by_dataone_designator,
      'SHA-224-bogus'
    )

  def test_020(self):
    """calculate_checksum_of_string()"""
    h = checksum.calculate_checksum_of_string('ateststring', 'MD5')
    self.assertEqual(h, 'c2572289c78add0e3192262cfd6b85ef')

  def test_030(self):
    """generate_from_flo(), XML serialization roundtrip"""
    for i in range(10):
      flo = StringIO.StringIO('ateststring')
      c1 = checksum.generate_from_flo(flo)
      c2 = dataoneTypes_v1.CreateFromDocument(c1.toxml())
      c = d1_common.checksum.get_checksum_calculator_by_dataone_designator(
        c2.algorithm
      )
      c.update('ateststring')
      self.assertEquals(c.hexdigest(), c2.value())

  def test_040(self):
    """generate_from_string(), XML serialization roundtrip"""
    for i in range(10):
      c1 = checksum.generate_from_string('ateststring')
      c2 = dataoneTypes_v1.CreateFromDocument(c1.toxml())
      c = d1_common.checksum.get_checksum_calculator_by_dataone_designator(
        c2.algorithm
      )
      c.update('ateststring')
      self.assertEquals(c.hexdigest(), c2.value())

  def test_050(self):
    """generate()"""
    for i in range(10):
      c = checksum.generate()
      self.assertTrue(isinstance(c, dataoneTypes_v1.Checksum))
      self.assertTrue(c.toxml())


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  unittest.main()
