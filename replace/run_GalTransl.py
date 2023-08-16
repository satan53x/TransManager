import os
import sys

from command import BulletMenu
from GalTransl import (
    AUTHOR,
    CONFIG_FILENAME,
    CONTRIBUTORS,
    GALTRANSL_VERSION,
    PROGRAM_SPLASH,
    TRANSLATOR_SUPPORTED,
)
from GalTransl.ConfigHelper import CProjectConfig
from GalTransl.Runner import run_galtransl

print(PROGRAM_SPLASH)
print(f"GalTransl version: {GALTRANSL_VERSION}")
print(f"Author: {AUTHOR}")
print(f"Contributors: {CONTRIBUTORS}\n")

INPUT_PROMPT = "请输入或拖入包含config.yaml的项目文件夹，或任意文件名的项目配置文件："

while True:
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input(INPUT_PROMPT)
    project_dir = os.path.abspath(path)
    config_file_name = CONFIG_FILENAME
    if project_dir.endswith(".yaml"):
        config_file_name = os.path.basename(project_dir)
        project_dir = os.path.dirname(project_dir)
    if not os.path.exists(os.path.join(project_dir, config_file_name)):
        print(f"项目文件夹内不存在配置文件{config_file_name}，请检查后重新输入\n")
        continue
    break

os.system("")  # 解决cmd的ANSI转义bug
if len(sys.argv) > 2:
    translator = sys.argv[2]
else:
    translator = BulletMenu("翻译器：", TRANSLATOR_SUPPORTED).run()

cfg = CProjectConfig(project_dir, config_file_name)
run_galtransl(cfg, translator)
print('Done.')