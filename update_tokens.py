import argparse
import hashlib
import json
import os
import re
import sys

HASH_LEN = 12
CHUNK = 65536

SOURCE_FILE = "_source.json"

# 与 Serein 端保持一致。两条都只拦明显的坏值，真正解析在 Go 侧
LIST_ENTRY_RE = re.compile(r"^[^/\\]+/" + re.escape(SOURCE_FILE) + r"$")
BARE_NAME_RE = re.compile(r"^[^/\\]+$")


def token(path):
    """文件内容的哈希前 HASH_LEN 位"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()[:HASH_LEN]


def find_sources(root):
    """遍历出所有 _source.json，跳过 . 开头的目录，结果按路径排序"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if SOURCE_FILE in filenames:
            out.append(os.path.join(dirpath, SOURCE_FILE))
    return sorted(out)


def write_json(path, obj):
    """按仓库既有格式落盘，4 空格缩进，不转义中文"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write("\n")


def process(path, apply_changes):
    """处理一个 _source.json，返回 是否改写、有没有问题、token 变了的文件名"""
    # 有问题时整个源不改写，调用方据此跳过
    # 遗留的顶层 version 字段会被丢掉，Serein 不读它
    rel = os.path.dirname(path)
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    problems = []

    # list 型的 files 是规则子源 marker 数组，不含 token，只校验不改写
    if d.get("type", "rules") == "list":
        for entry in d.get("files") or []:
            if not isinstance(entry, str) or not LIST_ENTRY_RE.match(entry):
                problems.append(f"规则子源条目 {entry!r} 不符合 <name>/{SOURCE_FILE}")
        return False, problems, []

    files = d.get("files")
    # 保持原顺序。files 里是不分大小写的字母序，跟 Python 默认的区分大小写
    # 排序不一样，BCUninstaller 与 balenaEtcher 换个位置，重排一次整份都会变
    # 重复项只去掉后面的，set 同样不保序
    if isinstance(files, dict):
        names = list(files)
    elif isinstance(files, list):
        names = list(dict.fromkeys(files))
    else:
        return False, ["files 既不是数组也不是对象，Serein 会拒绝该源"], []

    for n in names:
        if not BARE_NAME_RE.match(n):
            problems.append(f"{n!r} 含路径分隔符（files 只接受裸文件名）")
        elif n == SOURCE_FILE:
            problems.append(f"files 中出现 {SOURCE_FILE}，会覆盖版本标记")
        elif not os.path.isfile(os.path.join(rel, n)):
            problems.append(f"列出了 {n}，但文件不存在")

    if problems:
        return False, problems, []

    # 按原顺序重建。files 原本是数组时没有旧值可比，全部记作变化
    tokens = {}
    changed = []
    for n in names:
        t = token(os.path.join(rel, n))
        if not isinstance(files, dict) or files.get(n) != t:
            changed.append(n)
        tokens[n] = t

    new = {k: v for k, v in d.items() if k != "version"}
    new["files"] = tokens
    # 顺序不动过，token 又没变，内容相同就不写盘
    if new == d:
        return False, [], []

    if apply_changes:
        write_json(path, new)
    return True, [], changed


def main():
    ap = argparse.ArgumentParser(
        description="刷新规则源 _source.json 里每个规则文件的 token"
    )
    ap.add_argument(
        "root", nargs="?", default=None, help="仓库根目录，默认取脚本所在目录"
    )
    ap.add_argument(
        "--check", action="store_true", help="只校验不改写，有 token 需要刷新则退出码 1"
    )
    args = ap.parse_args()

    root = os.path.abspath(args.root or os.path.dirname(os.path.abspath(__file__)))
    sources = find_sources(root)
    if not sources:
        print(f"{root} 下没有找到 {SOURCE_FILE}", file=sys.stderr)
        return 1

    changed, nrules, bad = [], 0, 0
    for path in sources:
        name = os.path.relpath(path, root)
        try:
            did, problems, dirty = process(path, not args.check)
        except (json.JSONDecodeError, OSError) as e:
            print(f"{name}: 读取失败 {e}", file=sys.stderr)
            bad += 1
            continue
        for p in problems:
            print(f"{name}: {p}", file=sys.stderr)
        if problems:
            bad += 1
            continue
        with open(path, encoding="utf-8") as f:
            nrules += len(json.load(f).get("files") or [])
        if did:
            changed.append((name, dirty))

    if bad:
        print(f"\n{bad} 个源有问题，未改动", file=sys.stderr)
        return 1
    if changed:
        head = "需要更新 token" if args.check else "已更新 token"
        print(
            f"{head}，{len(changed)} 个源 / {sum(len(d) for _, d in changed)} 个规则文件："
        )
        for name, dirty in changed:
            print(f"  {name}")
            for f in dirty:
                print(f"    {f}")
        return 1 if args.check else 0
    print(f"token 均已是最新（{len(sources)} 个源 / {nrules} 个规则文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
