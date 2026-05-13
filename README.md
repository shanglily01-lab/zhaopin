# Web3 招聘平台

基于 FastAPI + MySQL（PyMySQL）+ Jinja2 + Tailwind CDN 的 Web3 招聘网站，实现企业职位发布与个人简历登记两大主流程。
表结构沿用既有数据库 `ty_zp`，配合 Gemini AI 助手与 Telegram 招聘群入口。

## 主要功能

| 模块 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `/` | Hero 搜索、热门职位、热门企业、平台数据 |
| 职位 | `/jobs`、`/jobs/{id}` | 关键词 / 远程 / 全职 / 急招 过滤、详情、投递 |
| 企业 | `/companies`、`/companies/{id}` | 列表 + 详情、在招职位、社交链接 |
| 人才 | `/resumes`、`/resumes/{id}` | 简历列表，未公开 / 未登录用户受限查看 |
| 注册 / 登录 | `/register`、`/login` | 区分企业 / 个人，企业自动建公司 |
| 个人控制台 | `/dashboard`、`/me/resume` | 编辑简历、查看投递记录 |
| 企业控制台 | `/dashboard`、`/me/company`、`/jobs/new` | 公司资料、发布 / 编辑职位、收件箱 |
| AI 助手 | `POST /api/jobs/polish`、`POST /api/resumes/polish` | Gemini 润色 JD / 个人优势 |
| TG 群 | 顶栏 + 页脚 | 跳转 `t.me/jobsofweb3` |

## 数据库表使用情况

| 表 | 用途 |
| --- | --- |
| `t_user` | 账号；`iscom` 区分个人 / 企业，企业 `cid` 关联 `t_company.id`，个人 `rid` 关联 `t_resume.id` |
| `t_company` | 公司资料、社交链接、规模 / 类型 / 主要链（字典） |
| `t_degree` | 职位（中英文名 / 远程 / 全职 / 急招 / 上下架 / 技能 / 薪资） |
| `t_resume` | 简历（昵称 / 期望 / 经验 / 学历 / 公开状态等） |
| `t_mess` | 投递记录：`sendid` 求职者，`uid` 收件人，`did` 职位 |
| `t_banner` / `t_trans2` / `t_sche` | 既有冗余数据，本期未写入，仍可读取展示 |

### 字典推断
仓库内无独立字典表，依据字段注释 + 真实分布，得出：

- `iscom`: 0 个人 / 1 企业
- `wrks`: 0 / 1001~1006（10 人以下 ~ 1000 人以上）
- `ctype`: 0 / 1 交易所 / 2 钱包 / 3 公链 / 4 DeFi / 5 媒体 / 6 投资 / 7 GameFi
- `edu`: 0 / 1000 高中 / 1001 大专 / 1002 本科 / 1003 硕士 / 1004 博士
- `exp`: 0 / 1000 1-3 年 / 1001 3-5 年 / 1002 5-10 年 / 1003 10+ / 1004 应届
- `isremote` (职位): 0 线下 / 1 远程 / 2 不限
- `isall` (职位): 0 兼职 / 1 全职 / 2 实习 / 3 外包
- `wtype` (简历): 0 / 1 / 2

如有官方字典口径，调整 `app/dicts.py` 即可，无需改动模板。

## 本地运行

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env（首次需要手动填）
copy .env.example .env
# 然后编辑 .env，把 DB_PASS / SECRET_KEY / GEMINI_API_KEY 等填上

# 3. 启动
python run.py
# 或：uvicorn app.main:app --host 0.0.0.0 --port 5020
```

打开 http://localhost:5020 即可访问。

## 线上部署（Linux + systemd + nginx）

完整步骤见 [`deploy/README.md`](deploy/README.md)。简版：

```bash
# 在服务器上
sudo mkdir -p /opt/zhaopin && sudo chown $USER:$USER /opt/zhaopin
git clone https://github.com/shanglily01-lab/zhaopin.git /opt/zhaopin
cd /opt/zhaopin && cp .env.example .env && vim .env       # 填真实凭据
bash deploy/deploy.sh

sudo cp deploy/zhaopin.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now zhaopin

sudo cp deploy/zhaopin.nginx.conf /etc/nginx/sites-available/zhaopin
sudo ln -s /etc/nginx/sites-available/zhaopin /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

之后升级只需 `cd /opt/zhaopin && bash deploy/deploy.sh`。

## 端到端测试

```powershell
python e2e_test.py
```

脚本会自动注册企业 + 个人账号，发布职位，创建简历，投递，校验双方控制台，全部断言通过会打印 `=== E2E PASS ===`。

## 项目结构

```
zhaopin/
  app/
    main.py              FastAPI 入口、错误处理
    config.py            读取 .env
    db.py                PyMySQL 连接 + fetch/execute
    dicts.py             字典 + 解析工具
    security.py          会话签名 + 密码兼容（bcrypt / md5 / 明文）
    ai.py                Gemini 润色
    templating.py        Jinja2 配置 + 自定义 filter
    routers/
      home.py            首页
      auth.py            注册 / 登录 / 退出
      jobs.py            职位 CRUD + AI 润色
      resumes.py         简历 CRUD + AI 润色
      companies.py       公司列表 / 详情 / 编辑
      dashboard.py       控制台 + 投递
    templates/           Jinja2 模板（基于 Tailwind CDN）
    static/css/app.css   补充样式
  uploads/               LOGO / 头像上传目录（运行时创建）
  run.py                 开发启动入口
  e2e_test.py            端到端流程脚本
  requirements.txt
  .env / .env.example
```

## 关于"通过 Google Stitch 完成页面设计"

页面使用 Tailwind + 自定义品牌色 / 圆角 / 阴影实现 Stitch 风格（白卡 + 微阴影 + 标签胶囊）。如需直接对接 Stitch 工具产出，可：

1. 在 Stitch 中以本项目 `app/templates/index.html` 等截图为参考生成 Figma 风格画板；
2. 把 Stitch 导出的色板 / 字号写入 `app/static/css/app.css` 顶部即可全局换肤。

页脚 + 顶栏均带有 Telegram 招聘群入口 `https://t.me/jobsofweb3`。

## 安全提示

- `.env` 中包含真实数据库与 API 凭据，已加入 `.gitignore`，请勿提交至公开仓库
- 登录使用 `itsdangerous` 签名 cookie；密码新存储为 bcrypt，并兼容历史 md5 / 明文以便老账号登录
- AI 接口失败时降级返回友好提示，不会中断主流程
