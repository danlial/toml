# -*- encoding: utf-8 -*-
import sys
import re
from datetime import datetime
import json

class StateMachine(object):
    # 初始状态
    init_state = 'init'
    # 当前状态机状态
    current_state = 'init'
    # 赋值状态：包括字符串、数组、float类型，此处特指: title = "TOML 例子" 这种情况
    assign_state = 'assign'
    # 多组键值对状态：特指字典类型，此处本程序暂时不考虑toml文本中的字典数组格式
    group_key_value_state = 'group'
    # 当前行的词元,token
    current_line_takens_list = []
    # 将toml格式转换成字典形式 最终存储地方
    to_json_dic = {}
    # 将toml格式转换成字典形式 临时存储地方
    runtime_dic = to_json_dic

    def __init__(self):
        try:
            self.tomfiledata = open("tomltestjson.toml", "rb")
            # 将文件的文本以行的形式加载到内存
            self.all_lines = self.tomfiledata.readlines()
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)
            raise RuntimeError('没有toml格式的配置文件tomltestjson，请检查')

    # 每次返回一行的词元 , self.all_lines 每次从列表里面pop弹出一行数据，直到处理完成
    def get_next_line_token(self):
        # 用来将每一行打成词元token
        PATTERN = re.compile(r"""(
        				^\[.*?\] |
        				".*?[^\\]?" | '.*?[^\\]?' |
        				\# |
        				\s | \] | \[ | \, | \s= |
        			)""", re.X)
        try:
            if self.all_lines:
                current_line = self.all_lines.pop(0)
                current_token_line = [p for p in PATTERN.split(current_line.strip()) if p.strip()]
                return current_token_line
            return []
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)
            # raise RuntimeError('no such toml file, check your toml file')

    def parse_toml_to_json(self):
        try:
            # 匹配赋值开头的
            assign_re = re.compile(r"[\w]+")
            # 匹配字典类型的
            group_re = re.compile(r"\[")
            while self.all_lines:
                current_token_line = self.get_next_line_token()
                if not current_token_line or current_token_line[0] =="#":
                    continue
                self.current_line_takens_list = current_token_line

                # 此处会用到状态机思想
                if self.current_state == self.init_state:
                    if assign_re.match(current_token_line[0]):
                        # 解析赋值状态这种情况
                        self.parse_assign()
                        self.current_state = self.assign_state
                    elif group_re.match(current_token_line[0]):
                        # 解析一群键值对的情况
                        self.parse_group()
                        self.current_state = self.group_key_value_state
                elif self.current_state == self.assign_state:
                    if assign_re.match(current_token_line[0]):
                        # 解析赋值状态这种情况
                        self.parse_assign()
                        self.current_state = self.assign_state
                    elif group_re.match(current_token_line[0]):
                        # 解析一群键值对的情况
                        self.parse_group()
                        self.current_state = self.group_key_value_state
                elif self.current_state == self.group_key_value_state:
                    if assign_re.match(current_token_line[0]):
                        # 解析赋值状态这种情况
                        self.parse_assign_group()
                        self.current_state = self.group_key_value_state
                    elif group_re.match(current_token_line[0]):
                        # 解析一群键值对的情况
                        self.parse_group()
                        self.current_state = self.group_key_value_state

            self.tomfiledata.close()
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    # 解析赋值状态这种情况
    def parse_assign(self):
        key = self.pop_tokens_list()
        if self.pop_tokens_list() != '=':
            raise Exception("配置文件错误")
        value = self.parse_value()
        self.to_json_dic[key] = value  # runtime_dic  to_json_dic

    def parse_assign_group(self):
        key = self.pop_tokens_list()
        if self.pop_tokens_list() != '=':
            raise Exception("配置文件错误")
        value = self.parse_value()
        self.runtime_dic[key] = value

    # 这是处理[xxx] 或者 [xxx.yyy]的情况
    def parse_group(self):
        key = self.pop_tokens_list()[1:-1]
        # print key
        temp = self.to_json_dic
        keys = key.split(".")
        # print type(keys)
        for index, value in enumerate(keys):
            # print value
            if value not in temp:
                # print type(value)
                temp[value] = {}
            temp = temp[value]
        self.runtime_dic = temp


    # 解析键值对的值，此处分别有字符串、时间、数组、整型、布尔类型
    def parse_value(self):
        # 字符串判断正则
        string_re = re.compile(r'(?:".*?[^\\]?")|(?:\'.*?[^\\]?\')')
        # 时间判断正则
        time_re = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
        # 数组判断正则
        array_re = re.compile(r'\[')
        # 整形判断正则
        int_re = re.compile(r'[+-]{,1}\d+')
        # 布尔判断正则
        boolean_re = re.compile(r'(^true$)|(^false$)')

        token = self.get_next_token()

        if string_re.match(token):
            return self.pop_tokens_list()[1:-1].decode('string-escape')
        elif time_re.match(token):
            time_ = time_re.match(self.pop_tokens_list()).group()
            return datetime.strptime(time_, "%Y-%m-%dT%H:%M:%SZ" ).strftime("%Y-%m-%d %H:%M:%S")
        elif int_re.match(token):
            int_ = int_re.match(self.pop_tokens_list()).group()
            return int(int_)
        elif boolean_re.match(token):
            boolean_ = boolean_re.match(self.pop_tokens_list()).group()
            return {'false':False,'true':True}[boolean_]
        elif array_re.match(token):
            array = []
            self.pop_tokens_list()
            while self.get_next_token() != ']':
                array.append(self.parse_value())
                if len(array) > 1 and  type(array[-1]) != type(array[0]):
                    raise Exception("数组的数据类型不一致")
                if self.get_next_token() != ',':
                    break
                self.pop_tokens_list()
            self.pop_tokens_list()
            return array

    # 依次从列表里面弹出数据，键、= 、 值所对应的token
    def pop_tokens_list(self):
        try:
            return self.current_line_takens_list.pop(0)
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    # 获取当前的下标为0的值， 但不弹出数据
    def get_next_token(self):
        try:
            return self.current_line_takens_list[0]
        except:
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)

    def to_print_json(self):
        try:
           self.parse_toml_to_json()
           print json.dumps(self.to_json_dic)

        except Exception as e :
            print e
            s = sys.exc_info()
            print "Error '%s' happened on line %d" % (s[1], s[2].tb_lineno)
