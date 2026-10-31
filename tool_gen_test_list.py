import json
import os
import re
import sys
import tomllib

OUT_FILE = "test0.toml"

# sort_key 用它把数字段切开
DIGIT_RUN_RE = re.compile(r"(\d+)")


# 排序键为不区分大小写的字母序，数字段按数值比
def sort_key(name):
    key = []
    for i, part in enumerate(DIGIT_RUN_RE.split(name)):
        if i % 2:
            key.append((0, int(part), ""))
        else:
            key.append((1, 0, part.lower()))
    return key


# 目录下全部规则文件，跳过 _deleted 与输出文件本身
def find_rules(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "_deleted"]
        for name in filenames:
            if name.endswith(".toml") and name != OUT_FILE:
                out.append(os.path.join(dirpath, name))
    return out


# 读出一份规则表的 app_id 与 info 段
def read_rule(path):
    with open(path, "rb") as f:
        d = tomllib.load(f)
    info = d["info"]
    return info["app_id"], info


# 平台顺序由规则本身决定，按出现次数从多到少排，次数相同按名字排
# 这样新增平台时不用改脚本，各平台在输出里的次序也保持一致
def platform_order(rules):
    count = {}
    for _, _, info in rules:
        for name in info["platforms"]:
            count[name] = count.get(name, 0) + 1
    return {
        name: i for i, name in enumerate(sorted(count, key=lambda n: (-count[n], n)))
    }


# 一段 [[tracker]]，source 与 name 放进注释，免得污染 Tracker 字段
def render(root, path, app_id, info, order):
    src = os.path.relpath(path, root).replace(os.sep, "/")
    platforms = sorted(info["platforms"], key=lambda n: order[n])
    return "\n".join(
        [
            f"# {info['name']}，{src}",
            "[[tracker]]",
            f"app_id = {json.dumps(app_id, ensure_ascii=False)}",
            f"platforms = {json.dumps(platforms, ensure_ascii=False)}",
        ]
    )


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    rules = []
    for path in find_rules(root):
        app_id, info = read_rule(path)
        rules.append((app_id, path, info))
    rules.sort(key=lambda x: sort_key(x[0]))

    order = platform_order(rules)
    blocks = [render(root, path, app_id, info, order) for app_id, path, info in rules]
    head = (
        "# Serein Tracker\n"
        "# 由 tool_gen_test_list.py 生成，请勿手动修改\n"
        "\n"
        'display_name = "测试"\n'
        "order = 999\n"
        'type = "app"\n'
    )
    text = head + "\n" + "\n\n".join(blocks) + "\n"

    with open(os.path.join(root, OUT_FILE), "w", encoding="utf-8") as f:
        f.write(text)

    entries = sum(len(info["platforms"]) for _, _, info in rules)
    print(f"已生成 {OUT_FILE}，{len(rules)} 个 Tracker 条目，{entries} 个平台条目")
    print(f"平台顺序：{' '.join(sorted(order, key=lambda n: order[n]))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
