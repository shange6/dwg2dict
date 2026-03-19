# -*- coding: utf-8 -*-
"""
@File        : dwg2dxf.py
@Author      : shange
@Time        : 2026-03-02 16:31
@Description : 106708617@qq.com
"""

"""
封装 ODA 转换，并修复转换后的韩文乱码问题
Args:
    dwg_path (str): 要转换的dwg文件路径
    dxf_dir (str): 转换后的文件存放目录
    fix_CODEPAGE (bool): 是否修复dxf文件的编码要求
Return: 
    str: 转换后的dxf文件路径

# 1. 安装ODA
https://www.opendesign.com/guestfiles/oda_file_converter

# 2. 安装ODA的运行库
sudo apt update
sudo apt install -y libxcb-xinerama0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxkbcommon-x11-0 \
libfontconfig1 libdbus-1-3 libglu1-mesa

# 3. 安装中文支持
sudo apt install language-pack-zh-hans -y
sudo locale-gen zh_CN.UTF-8

# 4. 安装中文字体 (解决 ODA 映射字体时的缺失问题)
sudo apt install fonts-wqy-microhei fonts-wqy-zenhei -y
还有一些依赖没有统计，根据实际情况添加

# 5. 设置当前环境变量
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
sudo locale-gen zh_CN.UTF-8

# 6. 在bash中执行的命令，xvfb-run -a强制使用虚拟显卡
xvfb-run -a /usr/bin/ODAFileConverter "/mnt/c/Users/panzheng/Desktop/1" "/home/panzheng/dwg/output_dxf" "ACAD2018" "DXF" "0" "1" "横向移动车.dwg"
/usr/bin/ODAFileConverter "/mnt/c/Users/panzheng/Desktop/1" "/home/panzheng/dwg/output_dxf/" "ACAD2018" "DXF" "0" "1" "横向移动车.dwg"
"""

import os
import re
import subprocess

def dwg2dxf(
        dwg_path: str, 
        dxf_dir: str=None,
        fix_CODEPAGE: bool=False
    ) -> str:

    dwg_path = os.path.abspath(dwg_path)
    dwg_dir = os.path.dirname(dwg_path)
    dwg_file = os.path.basename(dwg_path)
    root, ext = os.path.splitext(dwg_file)
    if ext == ".dxf": 
        return dwg_path
    if ext != ".dwg": 
        raise TypeError(f"{dwg_path}不是dwg文件")
    if not os.path.exists(dwg_path): 
        raise FileNotFoundError(f"没有发现{dwg_path}")
    if not dxf_dir:
        dxf_dir = dwg_dir
    else:
        dxf_dir = os.path.abspath(dxf_dir)
    if not os.path.exists(dxf_dir): 
        os.makedirs(dxf_dir, exist_ok=True)
    dxf_path = os.path.join(dxf_dir, f"{root}.dxf")

    # ODA转换命令 (ACAD2000/2004中文支持稳定)
    cmd = [
        # "xvfb-run -a",    # 强制使用虚拟显卡
        "ODAFileConverter",
        dwg_dir,
        dxf_dir,
        "ACAD2004", "DXF", "0", "1", dwg_file
    ]
    subprocess.run(
        cmd, 
        # env=env, 
        check=True, 
        capture_output=True
    )
    # 替换dxf文件中的编码为中文编码
    # 转换后的dxf文件编码不是中文的时候使用
    if fix_CODEPAGE:
        with open(dxf_path, 'r+', encoding='ascii', errors='ignore') as f:
            content = f.read()
            new_content = re.sub(               # 如果$DWGCODEPAGE存在则更改为中文编码
                r'(\$DWGCODEPAGE\s*3\s*)\w+',   
                r'\1ANSI_936', 
                content, 
                flags=re.MULTILINE
            )
            if '$SYSCODEPAGE' in new_content:   # 如果$SYSCODEPAGE存在则更改为中文编码
                new_content = re.sub(
                    r'(\$SYSCODEPAGE\s*3\s*)\w+', 
                    r'\1ANSI_936', 
                    new_content, 
                    flags=re.MULTILINE
                )
            else:
                new_content = re.sub(           # 如果$SYSCODEPAGE不存在则添加$DWGCODEPAGE
                    r'(\$DWGCODEPAGE\s*3\s*ANSI_936)',
                    r'\1\n$SYSCODEPAGE\n3\nANSI_936',
                    new_content,
                    flags=re.MULTILINE
                )
            f.seek(0)               # 指针移到开头
            f.write(new_content)    # 覆盖写入新内容
            f.truncate()            # 截断文件尾部
                
    return dxf_path

import ezdxf
import binascii
from typing import Dict, List, Any, Optional

class Dxf2List(object):
    """
    DXF 数据解析类，解析为bom列表和bom信息项
    功能：解析 DXF 文件中的 MTEXT 项目信息和 INSERT 块属性表格数据
    """

    # 正则表达式编译（提升性能）
    _pattern_blank = re.compile(r"\s+")
    _pattern_format = re.compile(r'\\[fFhHwWkK].*?;|[{}]|\\P')
    _pattern_m5 = re.compile(r'\\[Mm]\+5([0-9A-Fa-f]{4})')
    _pattern_unicode = re.compile(r'\\[Uu]\+?([0-9A-Fa-f]{4})')
    _pattern_contorl = re.compile(r'\\[^;]+;')

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
    
    def __init__(self, dxf_path: str, encoding: str = 'gbk'):
        self.dxf_path = dxf_path
        self.encoding = encoding
        self.boms = []              # bom列表
        self.log = []               # 解析日志，有错误则不能导入数据
        self.project_keys = {
            "项目代号": "project_code",
            "项目名称": "project_name",
            "合同号": "project_no",
        }
        self.project_code = None    # 项目代号
        self.project_name = None    # 项目名称
        self.project_no = None      # 合同号
        self.file_count = 0         # 文件个数
        self.parse()

    def log_add(self, msg: str, status: str="错误"):
        self.log.append({
            "status": status, 
            "msg": msg, 
            # "bom": {}
        })

    def _replace_hex(self, match: re.Match) -> str:
        """解析天河/天正及 Unicode 编码文本"""
        try:
            content = match.group(1)    # 判断匹配的是哪种模式            
            if "+5" in match.group(0):  # M+5 格式 (GBK)
                return binascii.unhexlify(content).decode('gbk')
            return chr(int(content, 16)) # Unicode 格式
        except Exception:
            return match.group(0)

    def _clean_text(self, text: str) -> str:
        """执行全套文本清洗流程"""
        if not text: return ""
        text = self._pattern_m5.sub(self._replace_hex, text)
        text = self._pattern_unicode.sub(self._replace_hex, text)
        text = self._pattern_format.sub("", text)
        # text = self._pattern_blank.sub("", text)
        text = self._pattern_contorl.sub("", text)
        return text

    def parse(self):
        """执行 DXF 深度解析"""
        try:
            doc = ezdxf.readfile(self.dxf_path, encoding=self.encoding)
            msp = doc.modelspace()
            self._parse_table_data(msp)     # 解析表格数据 (INSERT 块)
            self._parse_project_info(msp)   # 解析项目信息 (MTEXT)
        except Exception as e:
            self.log_add(f"文件读取失败: {str(e)}")

    def _parse_table_data(self, msp):
        """解析模型空间中的属性块数据"""
        for insert in msp.query("INSERT"):
            # 提取并清洗属性文本
            attr_texts = [self._clean_text(attr.dxf.text) for attr in insert.attribs]
            if not any(attr_texts): continue    # 过滤全空属性            
            match len(attr_texts):
                case 8: # 零件明细行                    
                    pos = insert.dxf.insert
                    attr_texts.extend([round(pos.x), round(pos.y)]) # 注入坐标
                    self.boms.append(dict(zip(self.bom_keys, attr_texts)))    # 映射到字典
                case 17: # 表格尾部信息页码
                    self.file_count += 1
                case _:
                    self.log_add(f"意外的属性长度 {len(attr_texts)} -> {attr_texts}")
        if self.boms:            
            self.boms.sort(key=lambda x: (x["x"], -x["y"])) # x轴增序，y轴降序

    def _parse_project_info(self, msp):
        """解析 MTEXT 中的项目元数据并校验一致性"""
        mtexts = msp.query("MTEXT")
        if self.file_count != len(mtexts):
            self.log_add(f"文件数({self.file_count})与页面数({len(mtexts)})不符")
        for mtext in mtexts:
            # print(mtext.dxf.text)
            chunks = self._clean_text(mtext.dxf.text).replace(":", "").replace("：", "").split()
            # print(chunks)
            for chunk in chunks:    # 按空格分割后的字符串
                for label, attr_name in self.project_keys.items():
                    if label in chunk:
                        new_value = chunk.replace(label, "").strip()
                        if not new_value: continue # 跳过空值
                        current_value = getattr(self, attr_name)                        
                        if current_value:  # 如果已存在
                            if current_value != new_value:  # 且值不一致，记录错误 
                                self.log_add(f"{label}不一致: {current_value} != {new_value}")
                        else:                            
                            setattr(self, attr_name, new_value) # 第一次发现，进行赋值


if __name__ == "__main__":
    # dwg_path = r"c:\users\panzheng\desktop\1\1.dwg"
    # dxf_path = dwg2dxf(dwg_path)
    dxf_path = r"c:\users\panzheng\desktop\1\3.dxf"
    dxf_data = Dxf2List(dxf_path)
    
    print(dxf_data.project_code)
    print(dxf_data.project_name)
    print(dxf_data.project_no)
    print(dxf_data.file_count)
    print(dxf_data.log)
    print(type(dxf_data.boms))
    