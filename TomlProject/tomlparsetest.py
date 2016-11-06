# -*- encoding: utf-8 -*-
import unittest
from statemachinejson import StateMachine
from statemachinexml import StateMachineXml
import sys

class TomlStateMachineTest(unittest.TestCase):

  # 初始化工作
  def setUp(self):
    pass

  # 退出清理工作
  def tearDown(self):
    pass

  # 具体的测试用例，一定要以test开头
  def test_to_print_json(self):
      try:
          StateMachine().to_print_json()
          pass
      except:
          s = sys.exc_info()
          print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

  def test_to_print_xml(self):
      try:
          StateMachineXml().print_to_xml();
      except:
          s = sys.exc_info()
          print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

if __name__ =='__main__':
  unittest.main()