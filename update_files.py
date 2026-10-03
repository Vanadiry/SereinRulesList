import argparse
import hashlib
import json
import os
import re
import sys

HASH_LEN = 12
CHUNK = 65536

SOURCE_FILE = "_source.json"

# sort_key 用它把数字段切出来
DIGIT_RUN_RE = re.compile(r"(\d+)")


# 规则表版本为文件内容的哈希前 HASH_LEN 位
def rule_version(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()[:HASH_LEN]


# 遍历出所有 _source.json，跳过 . 开头的目录，结果按路径排序
def find_sources(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if SOURCE_FILE in filenames:
            out.append(os.path.join(dirpath, SOURCE_FILE))
    return sorted(out)


# files 的排序键为不区分大小写的字母序，与仓库既有排布一致
# 数字段按数值比，让 dotnet6 排在 dotnet10 之前，逐位字符比会得到相反的次序
# re.split 带捕获组时按 文本/数字/文本/数字 交替，各段下标对齐
# 拼成同形状的元组就能直接比大小
def sort_key(name):
    key = []
    for i, part in enumerate(DIGIT_RUN_RE.split(name)):
        if i % 2:
            key.append((0, int(part), ""))
        else:
            key.append((1, 0, part.lower()))
    return key


# 目录下全部 .toml 规则文件，已排好序
def find_rules(rel):
    out = [n for n in os.listdir(rel) if n.endswith(".toml")]
    return sorted(out, key=sort_key)


# 目录下全部含 _source.json 的子目录，返回 <子目录>/_source.json，已排好序
def find_subdirs(rel):
    out = []
    for name in os.listdir(rel):
        path = os.path.join(rel, name)
        if not name.startswith(".") and os.path.isfile(os.path.join(path, SOURCE_FILE)):
            out.append(f"{name}/{SOURCE_FILE}")
    return sorted(out, key=sort_key)


# 按仓库既有格式落盘，4 空格缩进，不转义中文
def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write("\n")


# 两份 json 是否完全一致，键序也要一致
# Python 的 dict 相等只看键值对、忽略插入次序，files 换个顺序照样判相等
# 重排序就会静默不写盘；files 嵌在顶层，只比顶层键序不够，要递归下去比
def same_json(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return list(a) == list(b) and all(same_json(a[k], b[k]) for k in a)
    return a == b


# 比对重建前后的 files，逐行返回新增/更新、移除、顺序调整
def diff_files(old, new):
    old_keys, new_keys = list(old), list(new)
    # list 型源的 files 为数组，没有版本可比，只能判存在性
    old_map = old if isinstance(old, dict) else dict.fromkeys(old_keys)
    new_map = new if isinstance(new, dict) else dict.fromkeys(new_keys)

    lines = []
    for n in new_keys:
        if n not in old_map:
            lines.append(f"+ {n}")
        elif old_map[n] != new_map[n]:
            lines.append(f"~ {n} 版本 {old_map[n]} -> {new_map[n]}")
    lines += [f"- {n}" for n in old_keys if n not in new_map]
    # 次序不同也要报出来，否则重排会静默发生
    # 只比两边共有的那些，纯新增/移除带来的顺延不算重排
    if [n for n in old_keys if n in new_map] != [n for n in new_keys if n in old_map]:
        lines.append("~ 顺序已按字母序重排")
    return lines


# 处理一个 _source.json，返回 (变动说明列表, files 条数)，无变动时列表为 None
# 默认模式保持原顺序只刷版本，--all 才按磁盘重建；遗留的顶层 version 字段会被丢掉
def process(path, rebuild):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    old = d.get("files")
    new = {k: v for k, v in d.items() if k != "version"}

    if d.get("type", "rules") == "list":
        # list 型的 files 为规则子源 marker 数组，不含版本，默认模式无事可做
        if not rebuild:
            return None, len(old or [])
        new["files"] = find_subdirs(os.path.dirname(path))
    else:
        names = find_rules(os.path.dirname(path)) if rebuild else list(dict.fromkeys(old))
        new["files"] = {n: rule_version(os.path.join(os.path.dirname(path), n)) for n in names}

    if same_json(new, d):
        return None, len(new["files"])
    lines = diff_files(old, new["files"])
    write_json(path, new)
    return lines, len(new["files"])


def main():
    ap = argparse.ArgumentParser(description="维护规则源 _source.json 的 files 段")
    ap.add_argument(
        "--all",
        action="store_true",
        help="按磁盘上的规则文件完整重建 files，而非只刷新已列出的规则表版本",
    )
    args = ap.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    sources = find_sources(root)

    changed, nrules = [], 0
    for path in sources:
        lines, n = process(path, args.all)
        nrules += n
        if lines:
            changed.append((os.path.relpath(path, root), lines))

    if not changed:
        what = "files 与磁盘一致" if args.all else "规则表版本均已是最新"
        print(f"{what}，{len(sources)} 个源 / {nrules} 个规则文件")
        return 0

    head = "已重建 files" if args.all else "已更新规则表版本"
    print(f"{head}，{len(changed)} 个源 / {sum(len(l) for _, l in changed)} 处改动")
    for name, lines in changed:
        print(f"  {name}")
        for line in lines:
            print(f"    {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
