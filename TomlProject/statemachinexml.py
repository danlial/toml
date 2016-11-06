# -*- encoding: utf-8 -*-
import sys
import re
from datetime import datetime
import copy
from xml.dom.minidom import Document


class StateMachineXml(object):
    # 初始状态
    init_state = 'init'
    # 当前状态机状态
    current_state = 'init'
    # 字典状态
    dic_state = 'dic_state'
    # 基本KEY状态
    base_key_state = 'basekeystate'
    # 字符串值状态
    stri_value_state = 'stringstate'
    # 整数值状态
    int_value_state = 'intstate'
    # 布尔值状态
    boolean_value_state = 'booleanstate'
    # 时间值状态
    time_value_state = 'timestate'
    # 数组值状态
    array_value_state = 'arraystate'
    # =状态
    assign_state = 'assignstate'
    # \n换行状态 , 在数组值状态下，不会变成换行状态
    next_line_state = 'nextlinestate'
    # 空白行
    blank_state = 'blankstate'

    # 评论状态
    comment_state = 'commentstate'


    # 上次记录的索引
    previous_index = 0
    # 当前索引
    current_index = 0

    #
    char_list = []

    # 主XML节点

    def __init__(self):
        try:
            self.tomfile = open("tomltestxml.toml", "rb")
            self.tomfiledata = self.tomfile.read()
            # 将文件的文本以行的形式加载到内存
            self.sum = len(self.tomfiledata)
            self.doc = Document()
            self.toml = self.doc.createElement('toml')  # 创建根元素
            self.toml_copy = self.toml
            self.current_node = self.toml
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)
            raise RuntimeError('没有toml格式的配置文件tomltestxml，请检查')

    def parse_to_xml(self):
        try:
            for index in range(self.sum):

                if self.current_state == self.init_state or self.current_state == self.next_line_state:
                    # 这里都是处理key值得地方一种是基本数据类型的KEY，一种是字典类型的KEY
                    if self.tomfiledata[index] == '[':
                        self.current_state = self.dic_state
                        self.previous_index = index
                    if re.match('[a-zA-Z]' , self.tomfiledata[index]) :
                        self.current_state = self.base_key_state
                        self.previous_index = index
                    if self.tomfiledata[index] == '#':
                        self.current_state = self.comment_state
                    #
                elif self.current_state == self.base_key_state:
                    # 遇到空白的时候就能够生成完整的普通KEY
                    if self.tomfiledata[index] == ' ':
                        self.current_index = index
                        self.product_normal_key()
                        self.current_state = self.blank_state
                    # 遇到“=”改变状态为assign_state
                elif self.current_state == self.dic_state:
                    # 遇到]就生成字典类型的KEY
                    if self.tomfiledata[index] == ']':
                        self.current_index = index
                        self.parse_dic_key()
                    # 考虑遇到.的情况，这个时候是子级字典
                    if self.tomfiledata[index] == '\n':
                        self.current_state = self.next_line_state
                elif self.current_state == self.blank_state:
                    # 主要是作用于普通key后面的空白，下一个状态是=
                    if self.tomfiledata[index] == '=':
                        self.current_state = self.assign_state
                elif self.current_state == self.assign_state:
                    # 遇到“为字符串值状态
                    if self.tomfiledata[index] == '"':
                        self.previous_index = index
                        self.current_state = self.stri_value_state
                    # 遇到t or f 为布尔类型
                    if self.tomfiledata[index] == 't' or self.tomfiledata[index] == 'f' :
                        self.previous_index = index
                        self.char_list.append(self.tomfiledata[index])
                        self.current_state = self.boolean_value_state
                    # 遇到数字为整形值状态
                    if re.match("\d", self.tomfiledata[index]):
                        self.previous_index = index
                        self.char_list.append(self.tomfiledata[index])
                        self.current_state = self.int_value_state
                    # 遇到[为数组值类型
                    if self.tomfiledata[index] == '[':
                        self.previous_index = index
                        self.char_list.append(self.tomfiledata[index])
                        self.current_state = self.array_value_state
                #  ---------------------------上面和是其它状态分组， 下面全是值类型分组，为了方便阅读代码---------------------------------------
                elif self.current_state == self.stri_value_state:
                    # 遇到“为字符串值状态结束，形成完整的值 , 并在遇到‘\n’改变状态
                    if self.tomfiledata[index] == '"':
                        self.current_index = index
                        self.parse_str_value()
                    if self.tomfiledata[index] == '\n':
                        self.current_state = self.next_line_state
                elif self.current_state == self.int_value_state :
                    # 遇到空格整数值状态结束，形成完整的值 , 并在遇到‘\n’改变状态
                    if re.match("\d" , self.tomfiledata[index]):
                        self.char_list.append( self.tomfiledata[index])

                    if self.tomfiledata[index] == '\n':
                        self.parse_int_value()
                        self.current_state = self.next_line_state
                        self.char_list = []

                    # 遇到-的时候判定为时间状态
                    if self.tomfiledata[index] == '-':
                        self.current_state = self.time_value_state
                        self.char_list = []
                elif self.current_state == self.boolean_value_state:
                    # # 遇到空格布尔值状态结束，形成完整的值 , 并在遇到‘\n’改变状态
                    if re.match("[truefalse]", self.tomfiledata[index]):
                        self.char_list.append(self.tomfiledata[index])

                    if self.tomfiledata[index] == '\n':
                        self.parse_boolean_value()
                        self.current_state = self.next_line_state
                        self.char_list = []

                elif self.current_state == self.array_value_state :
                    # ‘数组类型有点特殊的地方是：可以跨行，这点要特殊处理， 结束的话暂时是考虑,使用相同数量的"[""]"
                    # 统计出[ 号的数量 ， 以及统计出]号的数量
                    left_brackets = 0
                    right_brackets = 0
                    for char in self.char_list:
                        if char == '[':
                            left_brackets +=1
                        elif char == ']':
                            right_brackets +=1

                    if left_brackets == right_brackets :
                        self.current_state = self.next_line_state
                        self.parse_array_value()
                        self.char_list = []
                    else:
                        self.char_list.append(self.tomfiledata[index])
                        if index == self.sum-1:
                            self.current_state = self.next_line_state
                            self.parse_array_value()
                            self.char_list = []
                elif self.current_state == self.time_value_state :                     # 值为时间的状态
                    if self.tomfiledata[index] == 'Z':
                        self.current_index = index+1
                        self.parse_time_value()

                    if self.tomfiledata[index] == '\n':
                        self.current_state = self.next_line_state
                elif self.current_state == self.comment_state :
                    if self.tomfiledata[index] == '\n':
                        self.current_state = self.next_line_state

        except  Exception:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def product_normal_key(self):
        try:
            normal_key = self.tomfiledata[self.previous_index : self.current_index]
            # print normal_key
            emlement = self.doc.createElement(normal_key)
            self.toml_copy.appendChild(emlement)
            self.current_node = emlement
        except Exception as e:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def parse_dic_key(self):
        try:
            temporary = self.toml
            dic_keys = self.tomfiledata[self.previous_index + 1: self.current_index]
            dic_keys_list = dic_keys.split(".")
            flag = True
            for index, dic_key in enumerate(dic_keys_list):
                if  temporary.childNodes :
                    for index1 , tem in enumerate(temporary.childNodes):
                        if tem.tagName == dic_key:
                            temporary = tem
                            flag = True
                            dic_key_element = tem
                            break
                        else:
                            flag = False
                    if flag is False:
                        dic_key_element = self.doc.createElement(dic_key)
                        temporary.appendChild(dic_key_element)
                        temporary = dic_key_element
                else:
                    dic_key_element = self.doc.createElement(dic_key)
                    temporary.appendChild(dic_key_element)
                    temporary = dic_key_element
            if dic_key_element :
                self.current_node = dic_key_element
                self.toml_copy = dic_key_element

        except :
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def parse_str_value(self):
        try:
            str_value = self.tomfiledata[self.previous_index + 1 : self.current_index]
            text_node = self.doc.createTextNode(str_value)
            self.current_node.appendChild(text_node)
        except :
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def parse_int_value(self):
        try:
            int_value = "".join(self.char_list)
            text_node = self.doc.createTextNode(int_value)
            self.current_node.appendChild(text_node)
            # self.char_list = []
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def parse_time_value(self):
        try:
            time_value = self.tomfiledata[self.previous_index : self.current_index]
            str_time_value = datetime.strptime(time_value, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
            text_node = self.doc.createTextNode(str_time_value)
            self.current_node.appendChild(text_node)
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def  parse_array_value(self):
        try:
            new_char_list = list(eval("".join(self.char_list)))
            length = len(new_char_list)
            for index in range(length):
                text_node = self.doc.createTextNode(str(new_char_list[index]))
                current_local_node = copy.deepcopy(self.current_node)
                self.current_node.appendChild(text_node)
                parent_node = self.current_node.parentNode
                self.current_node = current_local_node
                if index+1 != length :
                    parent_node.appendChild(self.current_node)



        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)


    def parse_boolean_value(self):
        try:
            bool = "".join(self.char_list)
            text_node = self.doc.createTextNode(bool)
            self.current_node.appendChild(text_node)
        except :
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)


    def print_to_xml(self):
        self.parse_to_xml()
        self.tomfile.close()
        print self.toml.toxml()

