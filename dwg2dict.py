import os
import re
import subprocess


def dwg2dxf(
        dwg_path: str, 
        dxf_dir: str=None,
        fix_CODEPAGE: bool=False
    ) -> str:
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

    if not os.path.exists(dwg_path): return f"Not found {dwg_path}"
    _, dwg_file_ext = os.path.splitext(dwg_path)
    if dwg_file_ext == ".dxf": return dwg_path
    if dwg_file_ext != ".dwg": return f"{dwg_path} is not dwg file"
    if dxf_dir: os.makedirs(dxf_dir, exist_ok=True)
    else: dxf_dir = os.path.dirname(dwg_path)
    dwg_dir = os.path.dirname(os.path.abspath(dwg_path))
    dwg_file = os.path.basename(dwg_path)
    dxf_path = os.path.join(dxf_dir, dwg_file.replace(".dwg", ".dxf"))

    # 1. 强制环境变量
    # env = os.environ.copy()
    # env["LC_ALL"] = "zh_CN.UTF-8"
    # env["LANG"] = "zh_CN.UTF-8"

    # 2. 使用ODA执行转换 (ACAD2000/2004中文支持稳定)
    cmd = [
        # "xvfb-run -a",    # 强制使用虚拟显卡
        "ODAFileConverter",
        dwg_dir,
        dxf_dir,
        "ACAD2004", "DXF", "0", "1", dwg_file
    ]
    try:
        subprocess.run(
            cmd, 
            # env=env, 
            check=True, 
            capture_output=True
        )


        # 3. 替换dxf文件中的编码为中文编码
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
            
    except subprocess.CalledProcessError as e:
        return f"{e.stderr.decode()}"    
    
    return dxf_path


import ezdxf
from ezdxf.math import Vec3
import binascii
pattern_blank = re.compile(r"\s+")
pattern_format = re.compile(r'\\[fFhHwWkK].*?;|[{}]|\\P')
pattern_m5 = re.compile(r'\\[Mm]\+5([0-9A-Fa-f]{4})')
pattern_unicode = re.compile(r'\\[Uu]\+?([0-9A-Fa-f]{4})')

# 处理天河/天正等插件特有的 \M+5XXXX 格式
def replace_hex(match: re.match):
    try:
        if match.re == pattern_m5:  # 替换天河/天正格式
            return binascii.unhexlify(match.group(1)).decode('gbk')
        if match.re == pattern_unicode: # 替换unicode格式
            return chr(int(match.group(1), 16))
    except:
        return match.group(0)

# 用正则表达式替换文本中的不需要字符
def replace_sub(text: str) -> str:
    text = pattern_m5.sub(replace_hex, text)
    text = pattern_unicode.sub(replace_hex, text)
    text = pattern_format.sub("", text)
    text = pattern_blank.sub("", text)
    return text

# 迭代处理字符串，提取key：value
def check_text(         # 把value拆分成{key: value}的格式，结果保存在project_info: dict中
        key: str,       # key是project_info_keys中的一个，当前没有传None
        value: str,     # key值对应的value，当前没有传要分析的字符串
        project_info: dict,     # 保存结果的字典
        project_info_keys: list # value中可能出现key
    ):
    for key1 in project_info_keys:
        if key1 in value:   # 字符串中包含key1
            project_info[key1] = value.split(key1)[1].replace("：", "")   # 添加字典项目key1：value1
            if key: # key是value的关键字，也就是上次循环的key1值
                # 如果value中包含一个key1，则说明value不是单纯的value,还包含了另一个key:value
                # 修改上次循环的key:value值, 去掉key1:value1
                project_info[key] =  value.split(key1)[0].replace("：", "") 
            # 把value去掉value1后的部分传给自己，做迭代运算
            return check_text(key1, project_info[key1], project_info, project_info_keys)

# 遍历MTEXT块，寻找项目信息
def get_project_info(doc) -> dict:
    """
    深度遍历 DXF，以汉字解析方式提取MTEXT
    Args:
        doc: dxf文件对象
    Return: 
        dict: 项目信息
    """
    project_info = {}
    project_info_bak = None     # 项目信息备份，用于与第二个项目信息进行比对
    project_info_keys = ["项目名称", "合同号", "部件名称" ,"部件数量", "数量"]  
    mtexts = doc.modelspace().query("MTEXT")
    project_info["文件数量"] = len(mtexts)  # 获取页数统计，与其他页数对比
    for mtext in mtexts:        # 获取真正的text文字，进行空格分隔
        for text in replace_sub(mtext.dxf.text).split():
            check_text(None, text, project_info, project_info_keys)
        if project_info_bak:    # 如果project_info_bak是有值的，也就说不是第一次循环
            if project_info_bak != project_info:
                msg = f"错误!!!项目信息不一致❌ {project_info_bak} {project_info}"
                dxf_data["info"].append(msg)
                print(msg)
        project_info_bak = project_info # 备份项目信息，方便下次进行比较
    return project_info

# 获取dxf文件数据
def dxf2dict(dxf_path: str) -> dict:
    """
    深度遍历 DXF，以汉字解析方式提取数据
    Args:
        dxf_path (str): 待解析的dxf文件路径
    Return: 
        dict: 解析后的数据
    """
    dxf_data = {}
    dxf_data["info"] = []   # 提取数据过程中发生的错误
    dxf_data_list = []
    dxf_data_keys = [
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
    doc = ezdxf.readfile(dxf_path, encoding='gbk')
    # 深度遍历模型空间中的 INSERT (块)
    for insert in doc.modelspace().query("INSERT"):
        block_name = insert.dxf.name            
        attr_text_list: list[str] = []
        for attr in insert.attribs:         # 提取属性文本 (ATTRIB)
            text = replace_sub(attr.dxf.text)
            attr_text_list.append(text)     # 过滤全部是空的文本
        if not all(item == "" for item in attr_text_list):                
            match len(attr_text_list):
                case 8:     # 处理表格内的每一行都是8位
                    x = round(insert.dxf.insert.x)
                    y = round(insert.dxf.insert.y)
                    attr_text_list.append(x)    # 添加坐标信息
                    attr_text_list.append(y)    # 添加坐标信息
                    attr_text_dict = dict(zip(dxf_data_keys, attr_text_list))
                    dxf_data_list.append(attr_text_dict)    # 转换为字典形式
                case 17:    # 处理表格尾部信息17位
                    page_count = dxf_data.get("文件个数", 0)
                    dxf_data["文件个数"] = page_count + 1
                    page_code = dxf_data.get("部件编号")
                    if page_code:
                        if page_code != attr_text_list[1]:
                            msg = f"错误!!!表格尾部编号不一致❌ {page_code} != {attr_text_list[1]}"
                            dxf_data["info"].append(msg)
                            print(msg)
                    else:
                        dxf_data["部件编号"] = attr_text_list[1]
                case _:
                    msg = f"错误!!!表格尾部信息个数❌ {attr_text_list}"
                    dxf_data["info"].append(msg)
                    print(msg)
        attr_text_list.clear()
    dxf_data_list.sort(key=lambda x: (x["x"], -x["y"])) # x轴增序，y轴降序
    dxf_data.update({"data": dxf_data_list})
    dxf_data["零件数量"] =  len(dxf_data_list)
    project_info = get_project_info(doc)
    if project_info["文件数量"] != dxf_data["文件个数"]:
        msg = f'错误!!!表格个数❌ {project_info["page_sum"]} != {dxf_data["page_count"]}'
        dxf_data["info"].append(msg)
        print(msg)
    dxf_data.update(project_info)
    return dxf_data

# 按位置顺序给data排序
# def sort_data(data: dict):
#     data.sort(key=lambda x: (x["x"], -x["y"]))
#     for item in data:
#         print(f'{item["code"]:40}, {item["spec"]:20}, {item["total_mass"]:10}, {item["x"]:30}, {item["y"]:30}')

if __name__ == "__main__":
    # dwg_path = "/mnt/c/Users/panzheng/Desktop/1/1.dwg"
    # dwg_path =  r"c:\users\panzheng\desktop\1\1.dwg"
    # dxf_path =dwg2dxf(dwg_path)
    # dxf_path = "/mnt/c/Users/panzheng/Desktop/1/1.dxf"
    dxf_path = r"c:\users\panzheng\desktop\1\2.dxf"
    dxf_data = dxf2dict(dxf_path)
    for item in dxf_data:
        if item == "data":
            for i in dxf_data[item]:
                print(i)
        else:
            print(item, dxf_data[item])
    print(len(dxf_data["data"]))