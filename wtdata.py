

# 把列表分成专用件列表和外购件列表两个部分
def split_datas(base_code: str, datas: list) -> tuple:     
    for i in range(len(datas)-1, -1, -1):   # 如果是专用件编码
        if is_comp_code(base_code, datas[i]["code"]):
            break
    return datas[:i + 1], datas[i + 1:]
    # buy = datas[i + 1:]         # 生成外购件列表
    # print(f"外购件共 {len(buy)} 件")
    # dedicated = datas[:i + 1]   # 生成专用件列表
    # print(f"专用件共 {len(dedicated)} 件")

def del_dedicated(base_code: str, dedicated: list) -> tuple:
    # 删除专用件列表中的杂项
    del_list = []           # 需要删除的列表
    info_list = []          # 需要返回的信息列表
    for j, v in enumerate(dedicated):
        if not is_comp_code(base_code, v["code"]):
            msg = f"删除专用件明细表中的外购件 {v["code"]:20} {v["spec"]:20}"
            info_list.append(msg)
            del_list.append(j)  # 收集需要删除的索引
            print(msg)
    for k in reversed(del_list):
        dedicated.pop(k)    # 执行删除
    return dedicated, info_list

# 标准化编码规则
def standard(code: str, base_code: str="") -> str:
    # code = code.replace(base_code, "")
    code = code.strip()
    code = code.replace("-", ".")
    code = code.replace("/", ".")
    return code

# 是否是部件的编码
def is_comp_code(base_code: str, code: str) -> bool:
    return code.startswith(base_code)
    return code != base_code and code.startswith(base_code)

# 比较两个列表在哪一级别相同, 从1开始数
def comp_list(prev_list: list, curr_list: list) -> int:  
    for index, (prev_code, curr_code) in enumerate(zip(prev_list, curr_list)):
        if prev_code == curr_code: continue
        else: return index
    return index + 1

import re
pattern = r'(\d+)'
# 自定义字符串转整形
def myint(code: str) -> int:
    try: return int(re.findall(pattern, code)[0])
    except Exception as e: print(e); return 0

# 自定义打印函数
def myprint(*args, sep=' ', end='\n', file=None, flush=False, isprint=False):
    if isprint:
        print_kwargs = {
            'sep': sep,
            'end': end,
            'file': file,
            'flush': flush
        }
        print(*args, **print_kwargs)

# 获取下一个连续子编码
def get_child_code(code: str) -> str:
    return code + ".1"

# 获取下一个连续同级编码
def get_next_peer_code(code: str) -> str: 
    # code = standard(code)
    code_list = code.split(".")
    new_seq = str(myint(code_list[-1]) + 1)
    return ".".join(code_list[:-1]) + "." + new_seq
# 获取下一个连续上级编码
def get_next_up_code(code: str, index: int=2) -> str: 
    # code = standard(code)
    code_list = code.split(".")
    new_seq = str(myint(code_list[-index]) + 1)
    return ".".join(code_list[:-index]) + "." + new_seq

# 获取第一个外购件万通码
def get_first_buy_code(code: str) -> str:    
    # code = standard(code)
    code_list = code.split(".")
    wtcode = ".".join(code_list[0:2])
    return wtcode + "." + str(myint(code_list[2]) + 1)

# 获取下一个连续外购件万通码
def get_next_buy_code(code: str) -> str:
    # code = standard(code)
    code_list = code.split(".")
    new_seq = str(myint(code_list[len(code_list) - 1]) + 1)
    code_list = code_list[:-1]
    code_list.append(new_seq)
    return ".".join(code_list)

# 比较两个编码的关系，返回元组（关系，万通码）
def generate_wtcode(prev_wtcode: str, prev_code: str, curr_code: str) -> tuple:
    # myprint(prev_wtcode, prev_code, curr_code)
    prev_code = standard(prev_code)
    curr_code = standard(curr_code)
    prev_code_list = prev_code.split(".")
    curr_code_list = curr_code.split(".")
    # 两个编码有同样级别的深度
    if len(curr_code_list) == len(prev_code_list):
        # 比较两个列表在哪个深度相同
        index = comp_list(prev_code_list, curr_code_list)
        if index == len(curr_code_list):
            wtcode = get_next_peer_code(prev_wtcode)
            myprint(f"{"完全相等的编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("same", wtcode)    # 完全相等的编码
        elif index == len(curr_code_list) - 1:
            if str(myint(prev_code_list[-1]) + 1) == curr_code_list[-1]:
                wtcode = get_next_peer_code(prev_wtcode)
                myprint(f"{"下一个连续编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
                return ("next", wtcode)# 下一个连续编码
            else:
                wtcode = get_next_peer_code(prev_wtcode)
                myprint(f"{"末级编码不相同不连续":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
                return ("peer", wtcode)# 末级编码不相同不连续
        else:
            wtcode = get_next_peer_code(prev_wtcode)
            myprint(f"{"多级编码不相同":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("some", wtcode)    # 多级编码不相同
    # 当前编码深度大于上一个编码深度，是下级编码
    if len(curr_code_list) > len(prev_code_list):
        if curr_code == prev_code + ".1":   # 连续子编码
            wtcode = get_child_code(prev_wtcode)
            myprint(f"{"连续子编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("child", wtcode)
        else:                               # 下级不连续编码
            wtcode = get_child_code(prev_wtcode)
            myprint(f"{"下级不连续编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("down", wtcode)
    # 当前编码深度小于上一个编码深度，是下级编码
    if len(curr_code_list) < len(prev_code_list):
        i = len(prev_code_list) - len(curr_code_list) + 1   # 连续编码差几个级别
        new_seq = str(myint(prev_code_list[len(curr_code_list) - 1]) + 1)
        prev_code_list = prev_code_list[:len(curr_code_list) - 1]
        prev_code_list.append(new_seq)
        if prev_code_list == curr_code_list:    # 上级连续编码
            wtcode = get_next_up_code(prev_wtcode, i)
            myprint(f"{"上级连续编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("upser", wtcode)
        else:                                       # 上级不连续编码
            wtcode = get_next_up_code(prev_wtcode, i)
            myprint(f"{"上级不连续编码":30} {prev_wtcode:30} {wtcode:30} {prev_code:30} {curr_code:30}")
            return ("upgap", wtcode)

# 检查数据并生成万通码
def getwtcode(res: dict) -> dict:
    base_code = res["data"][0]["code"]    # 第一个默认为部件名称和编号
    dedicated, buy = split_datas(base_code, res["data"])  # 分割列表为专用件和外购件
    msg = f"信息!!!零件数量共{res['零件数量']}件，其中专用件{len(dedicated)}件，外购件{len(buy)}件"
    res["info"].append(msg)
    print(msg)
    dedicated, info_list = del_dedicated(base_code, dedicated)  # 删除专用件中的杂项
    res["info"].extend(info_list)
    # 处理专用件列表
    dedicated[0]["wtcode"] = res["部件编号"]
    for m in range(1, len(dedicated)):
        _, dedicated[m]["wtcode"] = generate_wtcode(dedicated[m - 1]["wtcode"], dedicated[m - 1]["code"], dedicated[m]["code"])
    msg = f"信息!!!专用件列表还剩 {len(dedicated)} 件"
    res["info"].append(msg)
    print(msg)
    # 处理外购件列表
    if len(buy) > 0:    # 有外购件
        l = {'seq': '', 'code': '', 'spec': '外购件汇总', 'count': '1', 'material': '', 'unit_mass': '', 'total_mass': '', 'remark': '', 'x': '', 'y': ''}
        buy.insert(0, l)    # 给所有外购件加一个上级
        buy[0]["wtcode"] = get_first_buy_code(dedicated[len(dedicated) - 1]["wtcode"])
        buy[1]["wtcode"] = get_child_code(buy[0]["wtcode"])        
        for n in range(2, len(buy)):
            buy[n]["wtcode"] = get_next_buy_code(buy[n - 1]["wtcode"])
        res["data"] = dedicated + buy
    else: res["data"] = dedicated
    return res


if __name__ == "__main__":
    from dwg2dict import dwg2dxf, dxf2dict
    # dxf_path = "/mnt/c/Users/panzheng/Desktop/1/2.dxf"
    dxf_path = r"c:\users\panzheng\desktop\1\2.dxf"
    dxf_data = dxf2dict(dxf_path)
    dxf_data = getwtcode(dxf_data)
    # for index, item in enumerate(dxf_data["data"]):
    #     print(f"{index:10} {item}")
    