import argparse
import hashlib
import json
import os
import re
import sys

HASH_LEN = 12

SOURCE_FILE = "_source.json"

# 与 Serein 端一致的两条结构约束
LIST_ENTRY_RE = re.compile(r"^[^/\\]+/" + re.escape(SOURCE_FILE) + r"$")
BARE_NAME_RE = re.compile(r"^[^/\\]+$")


def token(path):
    """文件内容的哈希前 HASH_LEN 位。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:HASH_LEN]


def find_sources(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if SOURCE_FILE in filenames:
            out.append(os.path.join(dirpath, SOURCE_FILE))
    return sorted(out)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write("\n")


def process(path, apply_changes):
    """处理一个 _source.json。返回 (是否改写, 是否有问题)。"""
    rel = os.path.dirname(path)
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    problems = []

    # list 型：files 是子源 marker 数组，不含 token，只校验不改写
    if d.get("type", "rules") == "list":
        for entry in d.get("files") or []:
            if not isinstance(entry, str) or not LIST_ENTRY_RE.match(entry):
                problems.append(f"子源条目 {entry!r} 不符合 <name>/{SOURCE_FILE}")
        return False, problems

    files = d.get("files")
    if isinstance(files, list):
        names = sorted(set(files))
    elif isinstance(files, dict):
        names = sorted(files)
    else:
        return False, ["files 既不是数组也不是对象，Serein 会拒绝该源"]

    for n in names:
        if not BARE_NAME_RE.match(n):
            problems.append(f"{n!r} 含路径分隔符（files 只接受裸文件名）")
        elif n == SOURCE_FILE:
            problems.append(f"files 中出现 {SOURCE_FILE}，会覆盖版本标记")
        elif not os.path.isfile(os.path.join(rel, n)):
            problems.append(f"列出了 {n}，但文件不存在")

    if problems:
        return False, problems

    tokens = {n: token(os.path.join(rel, n)) for n in names}
    new = {k: v for k, v in d.items() if k != "version"}
    new["files"] = tokens
    if new == d:
        return False, []

    if apply_changes:
        write_json(path, new)
    return True, []


def main():
    ap = argparse.ArgumentParser(description="更新规则源 _source.json 的文件 token")
    ap.add_argument("root", nargs="?", default=None, help="根目录，默认脚本所在目录")
    ap.add_argument(
        "--check", action="store_true", help="只校验不改写，有差异则退出码 1"
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
            did, problems = process(path, not args.check)
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
            changed.append(name)

    if bad:
        print(f"\n{bad} 个源有问题，未改动", file=sys.stderr)
        return 1
    if args.check and changed:
        print(f"{len(changed)} 个源需要更新 token（--check 未写入）：")
        for c in changed:
            print("  " + c)
        return 1
    if changed:
        print(f"已更新 {len(changed)} 个源：")
        for c in changed:
            print("  " + c)
    else:
        print(f"token 均已是最新（{len(sources)} 个源 / {nrules} 个规则文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
