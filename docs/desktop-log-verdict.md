# Desktop 日志判定原理与实测记录

本文说明 `scripts/desktop/verdict.py` 的判定原理，并整理在本机日志中实际
观察到的全部情况。

适用读者：维护 Desktop 验证工具的人，以及需要判断"某个 UNKNOWN 到底是
什么原因"的人。

---

## 1. 一句话原理

**不问 Tableau「成功了吗」，而是读它自己写的结构化 JSON 日志，找两条特定记录。**

Tableau Desktop 把每个内部操作以 JSON Lines 格式写入日志。其中两条记录
恰好能区分成败：

| 结果 | 日志特征 | 匹配方式 |
| --- | --- | --- |
| 成功 | `k` = `end-workspace.load-workbook` | `k` 字段**精确等于** |
| 失败 | 记录里出现子串 `show-detailed-error-dialog` | **序列化后子串搜索** |

`verdict.py` 的核心就是这两行：

```python
if record.get("k") == "end-workspace.load-workbook":
    loaded = True
if "show-detailed-error-dialog" in text:
    error = True
```

**为什么检测方式不对称**：成功有专用事件名，失败没有。详见第 4 节。

---

## 2. 日志文件格式

每行是一个独立 JSON 对象：

```json
{"ts":"2026-10-08T19:23:34.306","pid":14528,"tid":"45c","sev":"info",
 "req":"-","sess":"-","site":"-","user":"-","x-b3-traceid":"-",
 "k":"end-workspace.load-workbook","l":{},"a":{...},"v":{}}
```

| 字段 | 含义 | 本工具是否使用 |
| --- | --- | --- |
| `ts` | 时间戳，毫秒精度，ISO 8601 | ✅ 用于过滤启动后的记录 |
| `pid` | 进程 ID | ✅ 用于归属判定 |
| `tid` | 线程 ID | ❌ |
| `sev` | 严重级别 | ❌ |
| `k` | 事件名（key） | ✅ 成功判定 |
| `v` | 负载，dict 或字符串 | ✅ 失败判定（搜子串） |
| `a` | 附加数据（耗时、内存等） | ❌ |

**时间戳是 ISO 8601 格式**，所以字符串比较等价于时间比较，不需要解析：

```python
if record.get("ts", "") >= since:
    yield record
```

---

## 3. 实测：一次成功加载的完整生命周期

以 `pid=14528`（ww08-dzv，LOADED）为例，按时间排序的关键事件：

```
19:23:29.267  启动，记录 argv[1] = 工作簿路径
19:23:30.145  begin-dom-parser.parse-xml-file          ← 解析 XML
19:23:30.169  end-dom-parser.parse-xml-file
19:23:33.375  begin-workbook-dom-loader.load-workbook-dom    ← DOM 加载
19:23:33.415  end-workbook-dom-loader.load-workbook-dom
19:23:33.417  begin-legacy-owning-workbook-lifecycle.parse-workbook
19:23:33.758  end-workbook-parser.parse                      ← 解析完成
19:23:34.306  end-workspace.load-workbook                    ★ 判定点
19:23:34.484  end-workspace.open-workbook
```

全程约 1 秒。注意 **`parse-workbook` 阶段存在**——这是成功与失败的关键
分水岭（见第 6 节）。

---

## 4. 成功与失败记录的实测结构对比

### 4.1 成功记录

```
k = end-workspace.load-workbook
v = {}                        ← 负载为空
a = {"depth":3, "elapsed":0.967, "exclusive":0.104, "id":"0GJhlN8AUFzJzvFxHCPsSN", ...}
```

有专用事件名，负载为空，所以必须用 `k` 精确匹配。

### 4.2 失败记录

```
k = begin-commands-controller.invoke-command     ← 通用命令调用，不是专用事件名
v = {"args": "tabdoc:show-detailed-error-dialog error-code-id=\"3538475634\"
      error-details=[\"*****\"] error-dialog-title=\"\"
      error-help-link=\"https://help.tableau.com/forward/producthelp?build=20262.26.0912.1023
        &edition=pro&errorcode=d2e8da72&lang=zh-cn&platform=windows
        &type=redirect&version=2026.2\"
      error-short-message=\"尝试加载工作簿 ... 时出错。加载无法成功完成。\"
      issue-helper-links=\"\" query-details=\"\" use-copy-command=\"true\""}
```

错误信息藏在通用记录的 `v.args` 里，没有专用事件名，所以只能在序列化
后的字符串里做子串搜索：

```python
text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
```

### 4.3 错误码对照

日志里 `error-code-id` 是**十进制**，`error-help-link` 里是**十六进制**：

```
error-code-id="3538475634"
hex(3538475634) = 0xd2e8da72   ← 与 errorcode=d2e8da72 一致
```

本机日志中出现的错误码统计（全部记录，27,281 条）：

| 错误码 | 十进制 | 出现次数 | 含义 |
| --- | --- | --- | --- |
| `d2e8da72` | 3538475634 | 3 | DOM loader 拒绝加载（manifest/元素缺陷） |

**只有这一个错误码**。说明本机遇到的"能通过 XSD 但打不开"全部是同一类根因。

---

## 5. 三个必须处理的陷阱

### 陷阱 1：日志是多个进程混合的

实测当前日志目录：

```
log.txt          2026-10-08T19:23:29 → 2026-10-08T19:25:23   pid 数=3
log_1.txt        2026-10-06T01:12:20 → 2026-10-06T23:28:58   pid 数=3
log_1_bk.txt     2026-09-28T15:54:51 → 2026-10-05T20:57:01   pid 数=5
log_2.txt        2026-10-05T20:56:55 → 2026-10-05T21:00:00   pid 数=1
log_3.txt        2026-10-05T20:59:35 → 2026-10-05T21:00:39   pid 数=1
log_bk.txt       2026-10-08T18:29:20 → 2026-10-08T18:37:50   pid 数=3
```

**一个日志文件里混着多个进程**（Tableau 是多进程架构：主进程 + `tabdoc`
+ `tabprotosrv`）。全部日志共出现 **16 个不同 pid**。

所以必须：

1. 在日志里找含 `argv[1]` 且含工作簿文件名的记录，拿到 pid
2. **只读该 pid 的记录**：`if record.get("pid") != pid: continue`

### 陷阱 2：日志轮转

Tableau 启动时把 `log.txt` 轮转成 `log_bk.txt`，旧的往后编号。**新记录
可能落在任何一个文件里**。

早期版本用"比较文件大小"找新增内容，**漏掉了轮转后的新文件**，报出大量
假 `UNKNOWN`。

正确做法：扫描所有 `log*.txt`，用时间戳过滤（第 2 节）。

### 陷阱 3：UNKNOWN 不能当通过

超时未匹配到特征 → `UNKNOWN`。策略是**重试，且一律当失败**：

```python
def test_with_retries(path, tries=3):
    for _ in range(tries):
        kill()
        verdict = test(path)
        if verdict != UNKNOWN:   # 只有拿到明确结论才返回
            return verdict
    return UNKNOWN
```

宁可重试也不猜。`verify_corpus.py` 把 UNKNOWN 计入失败。

### 附带：进程转发

Tableau 会把第二次启动**转发给已在运行的实例**。所以两次测试之间必须
`kill()` 并等待进程退出：

```python
def kill():
    # 杀 tableau / tabprotosrv / tabdoc
    # 轮询 tasklist 直到 tableau.exe 消失（最多 40 秒）
    time.sleep(4)   # 再等 4 秒确保文件句柄释放
```

---

## 6. 本机日志实测：三类情况全样本

把日志里**每个记录过 `argv[1]` 的 pid** 单独分析，得到完整分类。这是本机
15 个进程的实测结果：

| pid | 版本 | begin | end | parse | 错误对话框 | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| 14528 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 15640 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 22120 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 23320 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 2376 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 24472 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 3268 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 4728 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 5872 | 2026.2 | ✅ | ✅ | ✅ | — | LOADED |
| 20188 | 2026.2 | ✅ | ❌ | ❌ | ✅ | **FAIL** |
| 22828 | 2026.2 | ✅ | ❌ | ❌ | ✅ | **FAIL** |
| 5268 | 2026.2 | ✅ | ❌ | ❌ | ✅ | **FAIL** |
| 7420 | **2026.1** | ❌ | ❌ | ❌ | — | **UNKNOWN** |
| 20000 | **2026.1** | ❌ | ❌ | ❌ | — | **UNKNOWN** |
| 5864 | 2026.2 | ❌ | ❌ | ❌ | — | **UNKNOWN** |

（begin/end = `begin`/`end-workspace.load-workbook`，
parse = `end-legacy-owning-workbook-lifecycle.parse-workbook`）

**规则 100% 分离**：`end-workspace.load-workbook` 存在 ⟺ LOADED；
错误对话框存在 ⟺ FAIL。

### 6.1 情况 A：LOADED（9 个样本）

三个标志齐全，耗时约 1–1.8 秒。

### 6.2 情况 B：FAIL（3 个样本）

关键发现：**`end-workbook-dom-loader.load-workbook-dom` 在失败时也会触发**。

```
22:31:37.853  begin-workspace.load-workbook
22:31:37.877  begin-workbook-dom-loader.load-workbook-dom
22:31:37.921  end-workbook-dom-loader.load-workbook-dom     ← 这里"成功"了
              （然后弹错误对话框，没有 parse-workbook）
```

所以**不能**用 `end-workbook-dom-loader` 判定成功——它在两种情况下都出现。
必须用 `end-workspace.load-workbook`（在 `parse-workbook` 之后）。

失败发生在 `parse-workbook` **之前**，所以 `end-legacy-owning-workbook-
lifecycle.parse-workbook` 不存在。

**量化特征**（从 `begin-workspace.load-workbook` 到结束事件）：

| pid | 判定 | 耗时 | 结束事件 |
| --- | --- | --- | --- |
| 14528 | LOADED | 0.968 s | `end-workspace.load-workbook` |
| 22120 | LOADED | 1.799 s | `end-workspace.load-workbook` |
| 20188 | FAIL | **0.068 s** | `begin-commands-controller.invoke-command` |
| 22828 | FAIL | **0.073 s** | 同上 |
| 5268 | FAIL | **0.053 s** | 同上 |

**失败比成功快 15–30 倍**（~0.06 秒 vs ~1–1.8 秒）。因为失败在 DOM 阶段
就中断，不进入 parse/query/render。这也是为什么失败检测不需要等满
120 秒超时。

失败样本对应的三个工作簿：

| pid | 工作簿 |
| --- | --- |
| 20188 | `scratch/_w39_stc_only.twbx`（ww39 探针） |
| 22828 | `iterations/2026-02-15-ww06-null-safe-averages/...`（修复前） |
| 5268 | `scratch/_head/replicated-workbook.twbx`（ww06 探针） |

### 6.3 情况 C：UNKNOWN（3 个样本）——两种成因

**成因 1：Tableau 2026.1 无授权**（pid 7420、20000）

日志里混着两个版本：

```
2026.1: 2 个 pid  [7420, 20000]
2026.2: 14 个 pid [2376, 3268, 4728, 5268, 5864, 5872, 14528, 15640,
                   20188, 22120, 22604, 22828, 23320, 24472]
```

pid 7420 和 20000 的 `argv[0]` 是 `Tableau 2026.1\bin\tableau.exe`，而它们的
许可记录是：

```
JobProxy() created with no license file set
CriteriaCheck::GetMatchedLicense: Could not retrieve a valid license.
```

**2026.1 没有有效授权**，所以启动后卡在激活页，根本不进入加载流程——
没有 `begin-workspace.load-workbook`，永远不会有结论。

这印证了审计文档里的环境说明：

> Tableau Desktop **2026.1** on this machine has no valid license
> (`No License found for 'TableauDesktop'`) and stalls on the activation page,
> which must not be mistaken for a workbook failure.

**成因 2：进程只记录了 argv 就终止**（pid 5864）

pid 5864 是 2026.2，记录了 `argv[1]` 后只有 429 条记录（对比正常的 800+），
没有任何加载事件。属于启动后被 kill 或转发到其他实例。

**UNKNOWN 的正确处理**：重试；仍为 UNKNOWN 则计为失败。

---

## 7. 误报源：不能搜的关键词

### 7.1 `connector-plugin-error`（524 次）

日志里大量出现，但**与加载成败无关**：

```
Some connector plugins failed to load:
C:\Program Files\Tableau\Tableau 2026.2\bin\connectors\salesforce-uip.dll failed to load
Connector will not be overriden as it is already registered as a system connector: adb_mysql
...
```

实测：**LOADED 的 pid=14528 同样包含 `connector-plugin-error`**。

所以**绝不能**用「有 error 字样」判定失败。必须精确匹配
`show-detailed-error-dialog`。

### 7.2 许可相关记录（330 次）

`JobProxy() created with no license file set` 在**正常授权**的进程里也会
反复出现。只有 `CriteriaCheck::GetMatchedLicense: Could not retrieve a
valid license` 才是真问题。不能搜 `license`。

### 7.3 其他噪声

`crash-reporting`、`activity-and-resource-tracing-set-offs`、
`begin-central-widget.on-view-activated` 等事件名含关键词但与本判定无关。

日志中共有 **332 种**不同的 `k` 事件名。判定只依赖其中 2 个特征。

---

## 8. 为什么不用别的方法

| 方法 | 问题 |
| --- | --- |
| 看窗口标题 / 截图 | 需要 GUI 自动化；语言、主题、DPI 都会干扰 |
| 检查退出码 | Tableau 是常驻进程，加载失败**不退出** |
| 只看文件能否解压 | `.twbx` 是合法 zip，解压永远成功 |
| 只跑 XSD 校验 | **这正是踩过的坑**——XML 完全合法，Desktop 仍拒绝 |
| 检查 `end-workbook-dom-loader` | 失败时**也会触发**（第 6.2 节实测） |
| 用 Tableau 官方 API | 需要 Server/Cloud，不适用于本地文件打开验证 |
| 搜任意 `error` 字样 | 大量无关噪声（第 7 节） |

日志判定是唯一**可靠、无需 GUI、可自动化**的方式，而且它是 Tableau
自己的判定——不是我们猜的。

---

## 9. 判定流程伪代码

```
1. since = 当前时间（秒级，启动前）
2. 启动 tableau.exe <workbook>
3. 循环（最多 timeout=120 秒，每 2 秒检查一次）：
     for 每条 ts >= since 的记录（扫描所有 log*.txt）:
         text = 序列化(record.v)
         if pid 未定 且 文件名 in text 且 "argv[1]" in text:
             pid = record.pid          # 锁定目标进程
         if record.pid != pid: continue  # 忽略其他进程
         if record.k == "end-workspace.load-workbook":
             loaded = True
         if "show-detailed-error-dialog" in text:
             error = True
     if loaded or error: break
4. 判定：
     error            → FAIL
     loaded           → LOADED
     否则             → UNKNOWN（重试；仍 UNKNOWN 则计失败）
5. 终止进程；下一次测试前 kill() 并等待退出
```

---

## 10. 配置项

| 环境变量 | 用途 | 默认值 |
| --- | --- | --- |
| `TABLEAU_EXE` | 换用其他 Desktop 版本 | `C:\Program Files\Tableau\Tableau 2026.2\bin\tableau.exe` |
| `TABLEAU_LOG_DIR` | 换用其他日志目录 | 自动探测 |

日志目录自动探测（中英文两种）：

```
%USERPROFILE%\Documents\我的 Tableau 存储库\日志
%USERPROFILE%\Documents\My Tableau Repository\Logs
```

**换机器或换版本时必须确认**：目标版本的授权有效（第 6.3 节）。无授权的
版本会静默地永远返回 UNKNOWN。

---

## 11. 已知限制

1. **Windows 专属**：用了 `powershell` / `tasklist`。
2. **需要授权版本**：未授权的版本卡在激活页（第 6.3 节）。
3. **单实例串行**：必须 kill 后串行测试，不能并行（进程转发会混淆归属）。
4. **日志目录语言相关**：已探测中英文，其他语言需加候选路径。
5. **超时 120 秒**：极慢的机器或超大工作簿可能触发 UNKNOWN，需重试。

---

## 12. 相关文件

- `scripts/desktop/verdict.py` —— 判定内核（166 行，含上述全部注释）
- `scripts/desktop/check.py` —— 单文件封装
- `scripts/desktop/verify_corpus.py` —— 50 案例回归门禁
- `docs/cross-repo-desktop-workflow.md` —— 跨仓库工作流
- `docs/desktop-log-verdict.md` —— 本文（判定原理与实测记录）
- `docs/generated-twbx-desktop-load-audit.md` —— 根因与逐案例修复记录
