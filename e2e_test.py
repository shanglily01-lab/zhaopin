"""端到端流程测试：跑一遍注册/登录/发布/投递的核心路径。"""
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:5020"

ts = int(time.time())
COMPANY_USER = f"e2e_co_{ts}"
PERSONAL_USER = f"e2e_p_{ts}"
PASSWORD = "Test1234!"


def show(label: str, resp):
    print(f"\n--- {label} ---")
    print(f"  status: {resp.status_code}")
    if resp.history:
        print(f"  history: {[h.status_code for h in resp.history]} -> {resp.url}")


def main() -> None:
    # 1) 企业注册 + 登录
    s_co = requests.Session()
    r = s_co.post(f"{BASE}/register", data={
        "uname": COMPANY_USER, "upass": PASSWORD, "upass2": PASSWORD,
        "iscom": 1, "cname": f"E2E 测试公司 {ts}",
    }, allow_redirects=True)
    show("company register", r)
    assert r.status_code == 200, "company register failed"

    # 2) 完善公司资料
    r = s_co.post(f"{BASE}/me/company", data={
        "cname": f"E2E 测试公司 {ts}",
        "cnet": "https://example.com",
        "ctype": 1, "wrks": 1003, "chains": "2,4",
        "cim": "Building the future of Web3",
        "cdesc": "我们是一家专注于 Web3 基础设施的项目方。",
        "tg": "@e2e_test", "ws": "+8612345",
    }, allow_redirects=True)
    show("company profile save", r)
    assert r.status_code == 200

    # 3) 发布职位
    r = s_co.post(f"{BASE}/jobs/new", data={
        "dname": f"E2E Test Engineer {ts}",
        "cname": "测试工程师",
        "salary": "3000-5000 USDT",
        "waddr": "Remote",
        "skills": "Python FastAPI Web3 Solidity",
        "isremote": 1, "isall": 1, "urg": 1,
        "ddesc": "负责自动化测试。",
        "demark": "熟悉 Python / Web3。",
        "benefit": "全员持币",
    }, allow_redirects=True)
    show("job create", r)
    assert r.status_code == 200
    new_job_url = r.url
    job_id = int(new_job_url.rsplit("/", 1)[-1])
    print(f"  job_id={job_id}")
    s_co.close()

    # 4) 个人注册 + 登录
    s_p = requests.Session()
    r = s_p.post(f"{BASE}/register", data={
        "uname": PERSONAL_USER, "upass": PASSWORD, "upass2": PASSWORD,
        "iscom": 0,
    }, allow_redirects=True)
    show("personal register", r)
    assert r.status_code == 200

    # 5) 创建简历
    r = s_p.post(f"{BASE}/me/resume", data={
        "nick": f"e2e_候选人_{ts}",
        "addr": "远程",
        "degree": "Test Engineer",
        "cname": "测试工程师",
        "wtype": 1, "edu": 1002, "exp": 1001, "isen": 1, "isall": 1,
        "salary": "3500",
        "skills": "Python Selenium FastAPI",
        "pexp": "5 年测试经验，熟悉 Web3 项目。",
        "adv": "效率高，沟通好。",
        "ws": "+8612345", "tg": "@cand",
        "isvis": 1,
    }, allow_redirects=True)
    show("resume create", r)
    assert r.status_code == 200
    resume_url = r.url
    print(f"  resume_url={resume_url}")

    # 6) 投递职位
    r = s_p.post(f"{BASE}/jobs/{job_id}/apply", allow_redirects=True)
    show("apply job", r)
    assert r.status_code == 200

    # 7) 个人控制台应能看到投递记录
    r = s_p.get(f"{BASE}/dashboard")
    show("personal dashboard", r)
    assert "E2E Test Engineer" in r.text

    # 8) 注销并以企业身份查看面板
    s_p.close()
    s_co = requests.Session()
    r = s_co.post(f"{BASE}/login", data={"uname": COMPANY_USER, "upass": PASSWORD}, allow_redirects=True)
    show("company login", r)
    assert r.status_code == 200

    r = s_co.get(f"{BASE}/dashboard")
    show("company dashboard", r)
    assert PERSONAL_USER in r.text or "e2e_候选人" in r.text or "候选人" in r.text

    print("\n=== E2E PASS ===")


if __name__ == "__main__":
    main()
