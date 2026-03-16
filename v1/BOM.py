# -*- coding: utf-8 -*-
"""
@File        : newBOM.py
@Author      : shange
@Time        : 2026-03-07 09:23
@Description : 106708617@qq.com
"""


import re
from typing import Optional

class BaseBOM(object):
    # BOM类基类

    keys = [
        "project_code", # 项目代号
        "seq",          # 序号
        "code",         # 代号
        "spec",         # 名称
        "count",        # 数量
        "material",     # 材质
        "unit_mass",    # 单重
        "total_mass",   # 总重
        "remark",       # 备注
        "x",            # x坐标
        "y"             # y坐标
    ]

    material = {
        "钢板": r"(\d+)[xX×](\d+)[xX×](\d+)",   # 长x宽x厚
        "锰板": r"(\d+)[xX×](\d+)[xX×](\d+)",   # 长x宽x厚,
        "花纹板": r"(\d+)[xX×](\d+)[xX×](\d+)",   # 长x宽x厚,
        "不锈钢板": r"(\d+)[xX×](\d+)[xX×](\d+)",   # 长x宽x厚
        "圆管": r"[Φ∮](\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "Φ直径x厚,L=长度"
        "圆钢": r"[Φ∮](\d+)[,，  ]L=(\d+)",   # "Φ直径,L=长度",
        "方管": r"(\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "边长x厚,L=长度",
        "扁钢": r"(\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "宽x厚,L=长度",
        "H钢": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "边长x边长x厚,L=长度",
        "角钢": ["3#", "4#", "5#"],
        "槽钢": ["8#", "10#", "12#"],
        "轻轨": ["36#"],
        "重轨": ["36#"],
        "工字钢": ["10#", "14#"],
        "矩形管": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "长边x短边x厚,L=长度",
        "不等边角钢": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",   # "长边x短边x厚,L=长度",
    }

    def __init__(self, bom: dict):        
        self.bom = bom
        self.log = []
        self.check_all()
    
    def str2int(self, number: str) -> tuple[str, int]:
        # 字符串转换为整型，错误给出提示
        number = number.strip()
        if number.isdigit():
            return None, int(number)
        else:
            return f"{number}不是有效数字", None

    def check1more(self, number: int) -> str:
        # 检查整形变量是否小于1, ，错误给出提示
        if number >= 1: return None
        else: return f"{number}不能小于1"

    def str2float(self, number: str) -> tuple[str, Optional[int | float]]:
        # 字符串转换为整形或浮点型，错误给出提示
        msg, numeric = self.str2int(number)
        if not numeric:
            try:
                numeric = float(number)
                msg = None
            except:
                pass
        return msg, numeric

    def check0less(self, number: Optional[int | float]) -> str:
        # 检查整形H或浮点型变量是否大于0，错误给出提示
        if number > 0: return None
        else: return f"{number}必须大于0"

    def log_add(self, msg: str, status: str="错误"):
        self.log.append(f"{status}！！！{msg} {self.bom}")

    def check_all(self):
        self.check_keys()       # 检查keys是否一致
        self.check_seq()        # 检查序号
        self.check_spec()       # 检查名称是否规范
        self.convert_count()    # 转换数量为整形
        self.check_material()   # 检查材料
        self.check_remark()     # 检查备注
        self.convert_x()        # 转换x坐标
        self.convert_y()        # 转换y坐标

    def check_keys(self):         
        if set(self.bom.keys()) != set(self.keys):
            diff_keys = set(self.keys) - set(self.bom.keys())
            self.log_add(f"BOM缺少键:{sorted(diff_keys)}")

    def check_seq(self):
        # 检查序号
        pass

    def check_spec(self):        
        # 检查名称填写是否规范
        if not self.bom.get("spec") :
            self.log_add("名称不能为空")
            return

    def convert_number(
            self, 
            fun1: str,          # 转换为数字的函数
            key: str,           # 需要转换的key值
            fun2: str=None      # 判断是否大于0大于1的函数
        ) -> Optional[int | float]:
        # 转换为数字，并添加错误信息
        funcation1 = getattr(self, fun1)
        msg, numeric = funcation1(self.bom[key])
        if fun2: 
            funcation2 = getattr(self, fun2)
            if numeric: msg = funcation2(numeric)
        if msg: self.log_add(msg)
        return numeric

    def convert_count(self):
        # 转换数量为整形
        self.bom["count"] = self.convert_number("str2int", "count", "check1more")

    def check_material(self):
        # 检查材料
        pass

    def check_remark(self):
        # 检查备注
        if "借用" in self.bom["remark"]: self.bom["borrow"] = True      # 借用
        if "外购" in self.bom["remark"]: self.bom["procure"] = True     # 外购
        if "无图" in self.bom["remark"]: self.bom["noimage"] = True     # 无图
        if "附图" in self.bom["remark"]: self.bom["figure"] = True      # 附图

    def convert_x(self):
        # 转换坐标x
        self.bom["x"] = self.convert_number("str2float", "x")
        
    def convert_y(self):        
        # 转换坐标y
        self.bom["y"] = self.convert_number("str2float", "y")

class ProcureBOM(BaseBOM):
    # 外购件BOM类

    def get_parent_code(self):
        pass

class MiddleBOM(BaseBOM):
    # 中间件BOM类

    def check_all(self):
        super().check_all()
        self.check_code()           # 检查代号是否规范
        self.convert_unit_mass()    # 转换单重为浮点型
        self.convert_total_mass()   # 转换总重为浮点型
        self.check_mass()           # 检查数量关系是否正确

    def check_code(self):
        # 检查代号基本规范
        code = self.bom.get("code")
        if code:
            if not code[0].isalpha():
                self.log_add("代号必须以字母开头")
        else:
            self.log_add("代号不能为空")        
        pos = code.find(".")
        if pos == 0:  self.log_add("代号不能以点开头")

    def get_parent_sub_code(self, sub_code: str) -> str:
        # 获取父代号后半段
        for i in range(len(sub_code)-1, -1, -1):
            if sub_code[i] in ".-/":
                return sub_code[:i]
        self.log_add(f"{sub_code}获取父代号后半段")
        return None
    
    def check_spec(self):
        # 检查名称填写是否规范
        super().check_spec()
        spec = self.bom.get("spec") # 名称
        if not self.bom.get("noimage"): return  # 只检查无图件
        for key in self.material:
            if key in spec:     # 如果键在名称中
                print("物料名称：", key, end="  ")
                value = self.material[key]      # 正则表达式或列表
                if (isinstance(value, str)):    # 如果是字符串代表正则表达式
                    result = re.search(value, spec) # 搜索匹配的值
                    if result:
                        print("物料规格：", result.group(0), end="  ")
                        print("物料参数：", result.groups(), end="  ")
                        if "板" in key:
                            print("厚：", result.group(len(result.groups())), end="  ")
                        else:
                            print("厚：", result.group(len(result.groups()) - 1), end="  ")
                            print("长度：", result.group(len(result.groups())))
                elif (isinstance(value, list)): # 如果是列表代表是列表
                    for i in value:
                        if i in spec: print("型号：", i, end="  ")    # 找到型号
                    result = re.search(r"L=(\d+)", spec)    # 找到长度
                    if result:
                        print("长度：", result.group(1))

    def convert_unit_mass(self):
        if not self.bom["unit_mass"]: self.bom["unit_mass"] = self.bom["total_mass"]
        self.bom["unit_mass"] = self.convert_number("str2float", "unit_mass", "check0less")

    def convert_total_mass(self):
        self.bom["total_mass"] = self.convert_number("str2float", "total_mass", "check0less")

    def check_mass(self):
        # 检查数量重量关系
        if self.bom["count"] and self.bom["unit_mass"]:
            if self.bom["total_mass"] != self.bom["count"] * self.bom["unit_mass"]:
                self.log_add("数量重量关系")

class BorrowBOM(MiddleBOM):
    # 借用件BOM类
    pattern_char = r"[0-9./-]+"  # 匹配全部代号符号

    def check_remark(self):
        # 检查备注栏有没有父代号的数字部分
        super().check_remark()
        match = re.search(self.pattern_char, self.bom.get("remark"))
        if match:
            self.parent_sub_code = match.group(0)
        else:
            self.parent_sub_code = None

    def get_parent_code(self):
        if self.parent_sub_code:    # 借用栏有借用方后半段代号
            self.bom["parent_code"] = f"{self.bom.get("project_code")}.{self.parent_sub_code}"
        else:                       # 借用栏没有借用方后半段代号
            self.bom["parent_code"] = super().get_parent_sub_code(self.bom.get("code"))

    def check_code(self):
        # 检查代号是否规范
        super().check_code()
        self.get_parent_code()

class SpecialBOM(MiddleBOM):
    # 专用件BOM类
    
    def check_project_code(self, project_code: str):
        # 检查专用件代号是否以项目代号开头
        if project_code != self.bom.get("project_code"):
            self.log_add("代码不以项目代号开头")

    def check_sub_code(self, sub_code: str):
        # 检查备注栏的借用方代号是否规范
        if not sub_code: 
            self.log_add("代号后半段不能为空")
            return
        is_dot = False
        is_minus = False
        is_slash = False
        have_dot = False
        have_minus = False
        have_slash = False
        if sub_code[0] not in "123456789":
            self.log_add("代号后半段必须数字开头")
        if sub_code[-1] not in "0123456789":
            self.log_add("代号必须数字结尾")
        for i in sub_code:
            if i not in "0123456789.-/":
                self.log_add("代号含有其他字符")
            if is_dot or is_minus or is_slash:
                if i.isdigit(): pass
                else: self.log_add("符号后必须是数字")
            if have_minus:
                if i in ".-":
                    self.log_add("-后面不能有.-")
            if have_slash:
                if i in ".-/" :
                    self.log_add("/后面不能有.-/")
            # 为后面的循环准备数据状态
            if i == ".": 
                is_dot = True
                have_dot  = True
            else: 
                is_dot = False
            if i == "-": 
                is_minus = True
                have_minus  = True
            else: 
                is_minus = False
            if i == "/": 
                is_slash = True
                have_slash  = True
            else: 
                is_slash = False        

    def get_parent_code(self, sub_code):
        # 获取父代号
        parent_sub_code = super().get_parent_sub_code(sub_code)  # 获取父代号后半段
        if parent_sub_code:
            self.bom["parent_code"] = f"{self.bom.get("project_code")}.{parent_sub_code}"
        else:
            self.bom["parent_code"] = f"{self.bom.get("project_code")}"

    def check_code(self):
        # 检查代号是否规范
        super().check_code()
        code = self.bom.get("code")
        pos = code.find(".")
        if pos == -1: self.log_add("代号必须有点")
        project_code = code[:pos]
        sub_code = code[pos + 1:]
        # print("点的位置", pos)
        # print("项目代号", project_code)
        # print("代号后半段", sub_code)
        self.check_project_code(project_code)   # 检查专用件代号是否以项目代号开头
        self.check_sub_code(sub_code)           # 检查代号后半段
        self.get_parent_code(sub_code)          # 获取父代号

if __name__ == "__main__":
    bom1 = {
        "project_code": "ab",
        "seq": "",          # 序号
        "code": "a.1.2",         # 代号
        "spec": "H钢100x200x300，L=400",
        # "spec": "角钢3#L=500",
        "count": "2",        # 数量
        "material": "",     # 材质
        "unit_mass": "1.1",    # 单重
        "total_mass": "2.2",   # 总重
        "remark": "无图",       # 备注
        "x": "1",            # x坐标
        "y": "0"             # y坐标
    }
    # print(bom1)
    bom = SpecialBOM(bom1)
    # bom.check_all()
    for i in bom.log:
        print(i)
    print("父代码", bom.bom["parent_code"] )

