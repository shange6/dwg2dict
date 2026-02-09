


def list2tree(res: dict) -> dict:
    """
    将扁平BOM列表转换为树形结构
    :param flat_data: 包含 "wtcode" 的字典列表
    :return: 树形结构列表
    """
    # 1. 初始化：建立映射表，同时处理数值转换
    node_map = {}
    for item in res["data"]:
        # 深度拷贝，避免修改原始数据
        node = item.copy()
        # 初始化子项列表
        node["children"] = []
        # node.pop("seq")
        # node.pop("x")
        # node.pop("y")
        # 数值转换：处理空字符串情况，确保前端拿到的是数字
        node["count"] = int(node["count"]) if node.get("count") else 0
        if node["count"] == 0:
            msg = f"错误！！！数量不能为0❌ {node}"
            res["info"].append(msg)
            print(msg)
        node["unit_mass"] = float(node["unit_mass"]) if node.get("unit_mass") else 0.0
        node["total_mass"] = float(node["total_mass"]) if node.get("total_mass") else 0.0
        if node["unit_mass"] == 0:
            if node["total_mass"] != 0:
                if node["count"] == 1:
                    node["unit_mass"] = node["total_mass"]
                else:
                    msg = f"错误！！！单位重量不能为0❌ {node}"
                    res["info"].append(msg)
                    print(msg)
        else:
            if node["total_mass"] == 0:
                msg = f"错误！！！总重量不能为0❌ {node}"
                res["info"].append(msg)
                print(msg)
        # 将节点存入映射表，Key 为 wtcode
        node_map[node["wtcode"]] = node
 
    # 2. 核心逻辑：根据 wtcode 构建父子关系
    tree = []
    # 排序确保从顶级向下层构建
    for wtcode in sorted(node_map.keys()):
        current_node = node_map[wtcode]
        
        # 寻找父级 wtcode (例如 "A.3.1" 的父级是 "A.3")
        last_dot_index = wtcode.rfind(".")

        
        if last_dot_index == -1:
            # 没有点号，说明是顶级父项
            tree.append(current_node)
        else:
            # 截取父级 code
            parent_wtcode = wtcode[:last_dot_index]
            
            # 如果映射表里有这个父级，就挂载上去
            if parent_wtcode in node_map:
                node_map[parent_wtcode]["children"].append(current_node)
            else:
                # 找不到父级则提升为顶级
                tree.append(current_node)

    # 3. 后处理：清理没有子项的 children 字段
    def remove_empty_children(nodes):
        for n in nodes:
            if not n["children"]:
                del n["children"]
            else:
                remove_empty_children(n["children"])
                
    remove_empty_children(tree)
    res["data"] = tree
    return res

if __name__ == "__main__":
    import json
    from dwg2dict import dwg2dxf, dxf2dict
    from wtdata import getwtcode
    # dwg_path = "/mnt/c/Users/panzheng/Desktop/1/1.dwg"
    # dwg_path =  r"c:\users\panzheng\desktop\1\1.dwg"
    # dxf_path =dwg2dxf(dwg_path)
    dxf_path = r"c:\users\panzheng\desktop\1\2.dxf"
    dxf_data = dxf2dict(dxf_path)
    dxf_data = getwtcode(dxf_data)
    dxf_data = list2tree(dxf_data)
    print(json.dumps(dxf_data, indent=2, ensure_ascii=False))