# Tableau Cloud 凭证（PAT）存放与使用

本文说明抓取 Cloud 证据所需的 Tableau Cloud 个人访问令牌（PAT）放在哪里、
如何加载，以及哪些做法是禁止的。

## 1. 存放位置

凭证存在仓库**之外**的操作者私有文件里：

```
~/.config/wow-cloud/tableau.env
```

格式是 shell 风格的 `export KEY=VALUE`，每行一个：

```bash
export TABLEAU_SERVER_URL=https://<your-site>.online.tableau.com
export TABLEAU_SITE_ID=<site>
export TABLEAU_TOKEN_NAME=<pat-name>
export TABLEAU_TOKEN_SECRET=<pat-secret>
```

四个变量缺一不可：

| 变量 | 含义 |
| --- | --- |
| `TABLEAU_SERVER_URL` | 站点根 URL，例如 `https://10ax.online.tableau.com` |
| `TABLEAU_SITE_ID` | 站点标识（URL 里的 site 段） |
| `TABLEAU_TOKEN_NAME` | PAT 名称 |
| `TABLEAU_TOKEN_SECRET` | PAT 密钥（**真正的秘密**） |

### 权限要求

该文件必须**仅所有者可读写**。POSIX 上 `chmod 600`；Windows 上用
`icacls` 移除继承并只授予当前用户：

```powershell
icacls "%USERPROFILE%\.config\wow-cloud\tableau.env" /inheritance:r /grant:r "$env:USERNAME:(R,W)"
```

### 禁止事项

- **绝不**把 PAT 写进仓库、提交到 git、贴进 issue/PR、或写进 `case.yaml` /
  `evidence/`。这条与 `docs/ten-case-cloud-review.md` 一致：
  "Do not store the secret in the repository."
- **绝不**把密钥硬编码进脚本。`scripts/publish_to_cloud.py` 里的
  `TOKEN_SECRET` 默认值是空串，只能由环境提供。

## 2. 加载方式

脚本通过 `scripts/cloud_credentials.py` 解析凭证，解析顺序：

1. 已导出的进程环境变量（CI，或操作者自己 source 过）；
2. `WOW_CLOUD_ENV` 指定的文件（若该变量存在）；
3. 默认文件 `~/.config/wow-cloud/tableau.env`。

进程环境变量优先，所以 CI secret 或已 source 的会话不会被文件覆盖。

```python
from scripts.cloud_credentials import require_credentials

credentials = require_credentials()  # 缺失时抛出带修复指引的错误
auth = TSC.PersonalAccessTokenAuth(
    credentials["TABLEAU_TOKEN_NAME"],
    credentials["TABLEAU_TOKEN_SECRET"],
    site_id=credentials["TABLEAU_SITE_ID"],
)
```

`scripts/capture_case_cloud.py` 已经接入该加载器，所以**不再需要手动
`source`**：

```bash
python scripts/capture_case_cloud.py iterations/<id>/evidence/cloud-request.json
```

若确实想临时覆盖，仍可显式导出或指定文件：

```bash
WOW_CLOUD_ENV=/path/to/other.env python scripts/capture_case_cloud.py <request>
```

## 3. 验证凭证可用

```bash
python - <<'PY'
import sys; sys.path.insert(0, ".")
from scripts.cloud_credentials import require_credentials
import tableauserverclient as TSC
c = require_credentials()
auth = TSC.PersonalAccessTokenAuth(c["TABLEAU_TOKEN_NAME"], c["TABLEAU_TOKEN_SECRET"], site_id=c["TABLEAU_SITE_ID"])
server = TSC.Server(c["TABLEAU_SERVER_URL"], use_server_version=True)
with server.auth.sign_in(auth):
    print("sign-in OK", server.version)
PY
```

## 4. 轮换

PAT 泄露或过期时，在 Tableau Cloud 站点重建一个 token，只更新
`tableau.env` 的 `TABLEAU_TOKEN_SECRET` 即可；仓库侧无需改动。
