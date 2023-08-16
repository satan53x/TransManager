import os
import json
import csv

json_dir = "json_jp"  # JSON文件所在的目录
name_dict = {}  # 存储所有名字以及它们出现的次数的字典

# 遍历JSON文件所在的目录
for filename in os.listdir(json_dir):
    if filename.endswith(".json"):
        # 读取JSON文件
        with open(os.path.join(json_dir, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
        # 检索JSON文件中的名字
        for obj in data:
            if "name" in obj:
                name = obj["name"]
                if isinstance(name, str):
                    if name in name_dict:
                        name_dict[name] += 1
                    else:
                        name_dict[name] = 1
            if "names" in obj:
                names = obj["names"]
                if isinstance(names, list):
                    for name in names:
                        if isinstance(name, str):
                            if name in name_dict:
                                name_dict[name] += 1
                            else:
                                name_dict[name] = 1

# 将名字及其出现次数写入CSV文件
with open("人名替换表.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["JP_Name", "CN_Name", "Count"])  # 写入表头
    for name, count in name_dict.items():
        writer.writerow([name, "", count])

print("Done!")
