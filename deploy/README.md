# 部署指引（Linux + systemd + nginx）

适用：Ubuntu 22.04 / Debian 12 / 任意 systemd 发行版。

## 一、准备机器

```bash
# 基础依赖
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git nginx

# 应用目录（可改成 /var/www/zhaopin 等）
sudo mkdir -p /opt/zhaopin
sudo chown $USER:$USER /opt/zhaopin
```

## 二、拉代码 + 填配置

```bash
git clone https://github.com/shanglily01-lab/zhaopin.git /opt/zhaopin
cd /opt/zhaopin
cp .env.example .env
vim .env    # 填真实的 DB_HOST/DB_PASS/SECRET_KEY/GEMINI_API_KEY 等
```

> `.env` 不进 git，每台机器单独维护。

## 三、安装依赖 + 首次启动

```bash
bash deploy/deploy.sh
```

`deploy.sh` 会：建立 `.venv` → `pip install -r requirements.txt` → 提示安装 systemd unit。

## 四、安装 systemd 服务（开机自启 + 自动重启）

```bash
# 如果用 www-data 跑，请改 deploy/zhaopin.service 的 User= 字段；
# 也可以改成你自己的用户。文件目录用 /opt/zhaopin。

sudo cp deploy/zhaopin.service /etc/systemd/system/zhaopin.service
sudo systemctl daemon-reload
sudo systemctl enable --now zhaopin

# 验证
sudo systemctl status zhaopin
sudo journalctl -u zhaopin -f         # 看实时日志
curl -I http://127.0.0.1:5020/        # 应返回 200
```

## 五、配置 nginx（80 端口反代 + 静态资源直出）

```bash
sudo cp deploy/zhaopin.nginx.conf /etc/nginx/sites-available/zhaopin
sudo ln -s /etc/nginx/sites-available/zhaopin /etc/nginx/sites-enabled/zhaopin
# 改一下 server_name 为你的域名或公网 IP
sudo vim /etc/nginx/sites-available/zhaopin
sudo nginx -t && sudo systemctl reload nginx
```

## 六、HTTPS（可选，推荐）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

certbot 会自动改 nginx 配置 + 申请 Let's Encrypt 证书 + 续签 cron。

## 七、升级（拉新代码 -> 装依赖 -> 重启）

```bash
cd /opt/zhaopin
bash deploy/deploy.sh
```

## 八、回滚

```bash
cd /opt/zhaopin
git log --oneline | head             # 找上一版的 commit
git checkout <commit-sha>
bash deploy/deploy.sh
```

## 九、常见排错

| 现象 | 排查 |
| --- | --- |
| `systemctl status zhaopin` 失败 | `journalctl -u zhaopin -n 100` 看具体异常；80% 是 `.env` 缺字段 / 路径错 / 端口被占 |
| nginx 502 Bad Gateway | uvicorn 没起来。先 `curl http://127.0.0.1:5020/` 自己跑通 |
| 数据库连不上 | RDS 安全组要放行服务器公网 IP；改 `DB_HOST` 后 `systemctl restart zhaopin` |
| 修改了 `.env` 不生效 | systemd `EnvironmentFile` 在启动时读，必须 `systemctl restart zhaopin` |
| 想换端口 | 改 `deploy/zhaopin.service` 里的 `--port` 和 nginx 的 `proxy_pass` |
