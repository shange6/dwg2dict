# -*- coding: utf-8 -*-
"""
@File        : W.PY
@Author      : shange
@Time        : 2026-03-16 10:26
@Description : 106708617@qq.com
"""

import re
from typing import Dict, List, Any, Optional
from dwg2dxf2list import dwg2dxf, Dxf2List

class WTBOMS():
    # 万通 BOM 列表类

    class WTBOM(object):
        # 万通 BOM 融合类（工厂模式）

        def __new__(cls, bom: dict, project_code: str, first_code: str):
            remark = bom.get("remark", "")
            if "借用" in remark: target_cls = cls.BorrowBOM
            elif "外购" in remark: target_cls = cls.ProcureBOM
            else:  target_cls = cls.SpecialBOM        
            instance = object.__new__(target_cls)
            instance.__init__(bom, project_code, first_code)
            return instance

        class BaseBOM(object):
            # 万通 BOM 基类

            bom_keys = [
                "seq",          # 序号
                "code",         # 物料编码
                "spec",         # 物料规格
                "count",        # 数量
                "material",     # 材质
                "unit_mass",    # 单重
                "total_mass",   # 总重
                "remark",       # 备注
                "x",            # x坐标
                "y"             # y坐标
            ]

            log_bom_keys = [    # 写进log的项目
                # "seq",          # 序号
                "parent_code",  # 父代号
                "code",         # 物料编码
                "spec",         # 物料规格
                # "count",        # 数量
                # "material",     # 材质
                # "unit_mass",    # 单重
                # "total_mass",   # 总重
                "remark",       # 备注
                # "x",            # x坐标
                # "y"             # y坐标
            ]

            material = {
                "钢板": r"(\d+)[xX×](\d+)[xX×](\d+)",
                "锰板": r"(\d+)[xX×](\d+)[xX×](\d+)",
                "花纹板": r"(\d+)[xX×](\d+)[xX×](\d+)",
                "不锈钢板": r"(\d+)[xX×](\d+)[xX×](\d+)",
                "圆管": r"[Φ∮](\d+)[xX×](\d+)[,，  ]L=(\d+)",
                "圆钢": r"[Φ∮](\d+)[,，  ]L=(\d+)",
                "方管": r"(\d+)[xX×](\d+)[,，  ]L=(\d+)",
                "扁钢": r"(\d+)[xX×](\d+)[,，  ]L=(\d+)",
                "H钢": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",
                "角钢": ["3#", "4#", "5#"],
                "槽钢": ["8#", "10#", "12#"],
                "轻轨": ["36#"],
                "重轨": ["36#"],
                "工字钢": ["10#", "14#"],
                "矩形管": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",
                "不等边角钢": r"(\d+)[xX×](\d+)[xX×](\d+)[,，  ]L=(\d+)",
            }

            def __init__(self, bom: Dict, project_code: str, first_code: str):
                self.bom = bom
                for key, value in self.bom.items():
                    setattr(self, key, value)
                self.project_code = project_code
                self.first_code = first_code
                self.log = []
                self.check_all()

            def str2int(self, number: Optional[str | int]) -> tuple[str, int]:
                if isinstance(number, str):
                    number = number.strip()
                    if number.isdigit():
                        return None, int(number)
                elif isinstance(number, int):
                    return None, number
                return f"不是有效数字{number}", None

            def check1more(self, number: int) -> str:
                if number >= 1: return None
                else: return f"{number}不能小于1"

            def str2float(self, number: str) -> tuple[str, Optional[int | float]]:
                msg, numeric = self.str2int(number)
                if not numeric:
                    try:
                        numeric = float(number)
                        msg = None
                    except:
                        pass
                return msg, numeric

            def check0less(self, number: Optional[int | float]) -> str:
                if number > 0: return None
                else: return f"{number}必须大于0"

            def log_add(self, msg: str, status: str="错误"):
                self.log.append({
                    "status": status, 
                    "msg": msg, 
                    "bom": {k: self.bom.get(k) for k in self.log_bom_keys}
                })

            def check_all(self):
                self.check_keys()
                self.check_seq()
                self.check_spec()
                self.convert_count()
                self.check_material()
                self.check_remark()
                self.convert_x()
                self.convert_y()

            def check_keys(self):
                # 检查bom是否有全部的键
                diff = set(self.bom_keys) - set(self.bom.keys())
                if diff: self.log_add(f"BOM缺少键:{sorted(diff)}")

            def check_seq(self):
                pass

            def check_spec(self):        
                if not self.spec:
                    self.log_add("名称不能为空")
                    return

            def convert_number(
                    self, 
                    fun1: str, 
                    key: str, 
                    fun2: str=None
                ) -> Optional[int | float]:
                func1 = getattr(self, fun1)
                msg, num = func1(self.bom[key])
                if fun2 and num:
                    func2 = getattr(self, fun2)
                    msg = func2(num)
                if msg:
                    self.log_add(msg)
                return num

            def convert_count(self):
                self.bom["count"] = self.convert_number("str2int", "count", "check1more")

            def check_material(self):
                pass

            def check_remark(self):
                self.bom.update({
                    "borrow": "借用" in self.remark,
                    "procure": "外购" in self.remark,
                    "noimage": "无图" in self.remark,
                    "figure": "附图" in self.remark
                })

            def convert_x(self):
                self.bom["x"] = self.convert_number("str2float", "x")
                
            def convert_y(self):        
                self.bom["y"] = self.convert_number("str2float", "y")

        class ProcureBOM(BaseBOM):
            # 外购类

            def get_parent_code(self):
                self.bom["parent_code"] = self.first_code

            def check_all(self):
                super().check_all()
                self.get_parent_code()

        class MiddleBOM(BaseBOM):
            # 中间类

            def check_all(self):
                super().check_all()
                self.check_code()
                self.convert_unit_mass()
                self.convert_total_mass()
                self.check_mass()

            def check_code(self):
                # 检查代号是否规范
                if not self.code:
                    self.log_add("代号不能为空")
                    return
                if not self.code[0].isalpha():
                    self.log_add("代号必须以字母开头")

            def get_parent_sub_code(self, sub_code: str) -> str:
                # 获取父代号的后半段
                for i in range(len(sub_code)-1, -1, -1):
                    if sub_code[i] in ".-/":
                        return sub_code[:i]            
                return ""   # 如果没有后半段则为空
            
            def check_spec(self):
                # 检查名称是否规范
                super().check_spec()
                if not self.bom.get("noimage"):
                    return

            def convert_unit_mass(self):
                # 转换单重为数字
                if not self.bom["unit_mass"]:
                    self.bom["unit_mass"] = self.bom["total_mass"]
                self.bom["unit_mass"] = self.convert_number("str2float", "unit_mass", "check0less")

            def convert_total_mass(self):
                # 转换总重为数字
                self.bom["total_mass"] = self.convert_number("str2float", "total_mass", "check0less")

            def check_mass(self):
                # 检查数量重量关系是否正确
                c = self.bom["count"]
                u = self.bom["unit_mass"]
                t = self.bom["total_mass"]
                if c and u and t:
                    if abs(t - c * u) > 0.0001:
                        self.log_add("数量重量关系不正确")

        class BorrowBOM(MiddleBOM):
            # 借用类

            pattern_char = r"[0-9./-]+"

            def get_parent_code(self):
                # 借用件获取父代码
                # 获取备注的借用方代号后半段，如果没有备注则为空表示上级有借用
                match = re.search(self.pattern_char, self.remark)
                self.parent_sub_code = match.group(0) if match else None
                if self.parent_sub_code:    # 如果标注了借用方代码后半段
                    self.bom["parent_code"] = f"{self.project_code}.{self.parent_sub_code}"
                elif self.code == self.first_code:  # 如果是首行借用
                    self.bom["parent_code"] = self.project_code
                else:    # 如果没标注借用方代码后半段, 去掉最末部分就是父代码                
                    parent_sub_code = super().get_parent_sub_code(self.code)
                    if parent_sub_code:
                        self.bom["parent_code"] = super().get_parent_sub_code(self.code)
                    else:
                        self.log_add("借用件父代码为空")

            def check_code(self):
                super().check_code()
                self.get_parent_code()

        class SpecialBOM(MiddleBOM):
            # 专用类

            def check_project_code(self, project_code: str):
                # 检查项目代码是否规范
                if project_code != self.project_code:
                    self.log_add("代号不以项目代号开头")

            def check_sub_code(self, sub_code: str):
                # 检查后半段代码是否规范
                if not sub_code: 
                    self.log_add("代号后半段不能为空")
                    return
                
                # if sub_code[0] not in "123456789":
                #     self.log_add("代号后半段必须数字开头")
                match = re.match(r"\d+", sub_code)
                if not match: self.log_add("代号后半段必须数字开头")
                if sub_code[-1] not in "0123456789":
                    self.log_add("代号必须数字结尾")
                
                is_dot = is_minus = is_slash = False
                have_minus = have_slash = False

                for i in sub_code:
                    if i not in "0123456789.-/":
                        self.log_add("代号含有其他字符")

                    if (is_dot or is_minus or is_slash) and not i.isdigit():
                        self.log_add("符号后必须是数字")

                    if have_minus and i in ".-":
                        self.log_add("代号中-后面不能有.-")
                    if have_slash and i in ".-/":
                        self.log_add("代号中/后面不能有.-/")

                    is_dot = i == "."
                    is_minus = i == "-"
                    is_slash = i == "/"
                    have_minus |= is_minus
                    have_slash |= is_slash

            def get_parent_code(self, sub_code):
                # 获取专用件父代码
                parent_sub_code = super().get_parent_sub_code(sub_code)
                if parent_sub_code: # 如果父代码后半段不是空
                    self.bom["parent_code"] = f"{self.project_code}.{parent_sub_code}"
                else:               # 如果父代码后半段是空
                    self.bom["parent_code"] = f"{self.project_code}"

            def check_code(self):
                # 检查代码是否规范
                super().check_code()
                pos = self.code.find(".")
                if pos == -1: self.log_add("专用件代号必须有点")
                project_code = self.code[:pos]
                sub_code = self.code[pos+1:]
                self.check_project_code(project_code)
                self.check_sub_code(sub_code)
                self.get_parent_code(sub_code)

    def __init__(self, data: Dxf2List):
        self.boms = data.boms
        self.log = data.log     # 继承Dxf2List的log信息
        self.project_code = data.project_code
        self.project_name = data.project_name
        self.project_no = data.project_no
        self.file_count = data.file_count
        self.first_code = self.boms[0]["code"]
        self.check_all()

    def log_add(self, msg: str, item: WTBOM, status: str="错误"):
        self.log.append({
            "status": status, 
            "msg": msg, 
            "bom": {k: item.bom.get(k) for k in self.WTBOM.BaseBOM.log_bom_keys}
        })

    def check_all(self):
        # 检查全部
        code_set = set()
        code_list = [item.get("code") for item in self.boms]
        code_list.append(self.project_code)
        for bom in self.boms:
            item = self.WTBOM(bom, self.project_code, self.first_code)
            # 检查专用件代号重复
            if item.code in code_set:
                if not (item.bom.get("borrow") or item.bom.get("procure")):
                    self.log_add(f"专用件代号不能重复", item)
            else:
                code_set.add(item.code)
            # 检查父代号存在
            if item.bom.get("parent_code") not in code_list:
                self.log_add(f"父代号不存在", item)
            # 导入WTBOM的log信息
            self.log.extend(item.log)   # 继承WTBOM的log信息

if __name__ == "__main__":
    # dwg_path = r"c:\users\panzheng\desktop\1\1.dwg"
    # dxf_path = dwg2dxf(dwg_path)
    dxf_path = r"c:\users\panzheng\desktop\1\2.dxf"
    res = WTBOMS(Dxf2List(dxf_path))
    # print(res.log)
    for i in res.log:
        print(i)
    print(res.project_code)
    print(res.project_name)
    print(res.project_no)
    print(res.file_count)
    