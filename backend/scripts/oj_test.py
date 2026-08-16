"""OJ 客户端连通性自测脚本。

从 backend/.env 读取 OJ 凭据（OJ_API_BASE / OJ_USERNAME / OJ_PASSWORD），
不在代码中硬编码任何敏感信息。只打印测试结果，不打印密码。

用法（在 backend/ 目录下）：
    python scripts/oj_test.py              # 只测登录 + 拉取题目标题
    python scripts/oj_test.py --submit     # 额外提交一次 A+B（P1000）并轮询结果
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clients.oj_client import OJClient  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="BUCTOJ 客户端自测")
    parser.add_argument("--submit", action="store_true", help="提交一次 A+B 并轮询结果")
    args = parser.parse_args()

    oj = OJClient()
    if not oj.enabled:
        print("[✗] 未配置 OJ 凭据，请在 backend/.env 填写 OJ_API_BASE / OJ_USERNAME / OJ_PASSWORD")
        return

    print(f"[i] OJ 地址: {oj.base}")
    print(f"[i] 账号: {oj.username}")

    print("[1/3] 测试登录 ...")
    ok = oj.login()
    print("      登录结果:", "成功" if ok else "失败")
    if not ok:
        return

    print("[2/3] 拉取题目 P1000 标题 ...")
    prob = oj.fetch_problem(1000)
    print("      题目:", prob.get("title") or "(未取到)")

    if not args.submit:
        print("[3/3] 跳过提交（加 --submit 可实测判题链路）")
        return

    print("[3/3] 提交 A+B（Python）并轮询 ...")
    code = "a, b = map(int, input().split())\nprint(a + b)\n"
    result = oj.judge(code, language="python", problem_id=1000)
    print("      solution_id:", result.get("solution_id"))
    print("      result_code:", result.get("result_code"))
    print("      结果:", result.get("label"))
    print("      通过率:", result.get("pass_rate"))
    print("      是否通过:", result.get("accepted"))

    sid = result.get("solution_id")
    if sid:
        sim = oj.get_similarity(sid)
        print("      查重记录:", sim)

    oj.close()


if __name__ == "__main__":
    main()
