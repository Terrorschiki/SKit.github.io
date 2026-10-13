# SKit 报价网站项目 — 经验沉淀

> 一次完整实战：把一个五金/厨具公司的三份 Excel 报价单，做成 445 款产品的**四语静态报价网站**，并发布到 GitHub Pages。
> 本文记录**可复用的方法**和**踩过的坑**，供同类项目直接照抄或避坑。

---

## 0. 项目速览

| 项目 | 内容 |
|---|---|
| 输入 | 3 份供应商报价单（xlsx，内嵌产品实拍图）+ 3 份同内容 PDF + 12 张影棚封面图 |
| 规模 | 445 款产品（L柄 119 / P柄 119 / 硅胶尼龙 207），1338 张产品图，96 张封面图 |
| 技术栈 | 纯静态 HTML/CSS/JS（零运行时依赖）+ Python 构建脚本 |
| 语言 | 英 / 西 / 法 / 中（203 条词典 × 4） |
| 发布 | GitHub Pages（组织仓库 `Terrorschiki/SKit.github.io`，Actions 部署） |
| 产物 | 1902 个文件 / 276.5 MB |
| 线上 | https://terrorschiki.github.io/SKit.github.io/ |

**目录约定**（踩坑后定型，见 §4.1）：

```
仓库根目录/                 ← GitHub Pages 直接从这里提供服务
├── .github/workflows/pages.yml   ← 必须在根目录，否则不生效
├── index.html collections.html about.html …   ← 网站页面
├── assets/{css,js,img,data,products}/
├── data/catalog.json       ← 前端拉取的产品数据
├── collections/ products/ downloads/
├── .nojekyll
├── _build/                 ← Python 构建脚本（不进产物）
└── site/                   ← 构建暂存区（gitignore）
```

---

## 1. 从 Excel 报价单提取数据

### 1.1 先摸清结构，别急着写解析

三份表**列结构并不一致**，必须分别处理：

| 文件 | 结构差异 |
|---|---|
| L柄 / P柄 | 品名单元格内嵌货号，中英双语用 `\n` 分隔：`叉/L01\nFork` |
| 硅胶尼龙 | 货号独立成列（`货号`），品名纯中文，另多一列 `颜色` |

解析前先导出原始单元格看一眼，确认：表头行号、数据起始行、合并单元格、列偏移。

```python
import openpyxl
wb = openpyxl.load_workbook(path, data_only=True)   # data_only 取缓存值
ws = wb.active
for r in range(1, 6):
    print(r, [ws.cell(r, c).value for c in range(1, ws.max_column + 1)])
```

### 1.2 列名映射（厨具报价单通用）

`品名→名称`、`包装方式→packing`、`价格→USD单价`、`装箱数→每箱数量`、`尺寸→size`、
`毛重→gross weight`、`材质→material`、`体积→CBM`、`备注→内包装`、`颜色→colour`

### 1.3 货号解析：正则回溯陷阱

品名里的货号格式很杂：`L01`、`M-P01`、`1-P110`、`P113`、`3305E`。

**踩坑**：这个正则在 `M-P68` 上会失败：

```python
# ❌ 错：[A-Za-z]{1,3} 会贪婪吃掉 "M-P"，然后 -? 匹配空格，\d 撞上 "-" 失败
r"^(?:\d{1,2}-)?[A-Za-z]{1,3}-?\d{1,4}[A-Za-z]?$"

# ✅ 对：把字母块和连字符拆成互不重叠的两段
TOKEN_CODE_RE = re.compile(
    r"^(?:\d{1,2}-)?"          # 可选数字前缀，1-P110
    r"[A-Za-z]{1,3}"           # L / P / MP / SK
    r"(?:-[A-Za-z]{1,2})?"     # 可选第二字母块，M-P68
    r"-?\d{1,4}"               # 数字
    r"[A-Za-z]?$"              # 可选尾字母，3305E
)
```

**通用教训**：当正则里相邻的两个子模式都能匹配同一字符时（`[A-Za-z]` 能匹配 `-` 吗？不能，
但 `{1,3}` 的贪婪让引擎先吃完再回溯，回溯路径走不通就整体失败），把可选结构显式拆开，
并用真实样本做单元测试。**写完正则一定跑一次全量样本**，别只看第一行。

### 1.4 品名拆解：用 `/` 和换行双分隔符

```python
lines = [l for l in clean_text(raw).split("\n") if l.strip()]
parts = [p.strip() for ln in lines for p in ln.split("/") if p.strip()]
# 逐 token 判断：是货号？含中文？是尺寸注记？→ 分派到 code / zh / en / size
```

尺寸注记要处理全角括号和尾部粘连：`M-P68（6cm)`、`线漏16CM` → size=`16CM`。

### 1.5 中文表补英文名

硅胶尼龙表 207 款全是中文品名。做法不是机翻，而是**词典化重组**：

```
<柄型> + <材质> + <器型> + <尺寸/套装>
榉木柄硅胶意粉勺 → Silicone spaghetti server, Beech wood handle
```

要点：
- 柄型/材质/器型各维护一张表，**按长度倒序匹配**（`大圆漏` 必须优先于 `漏`）
- 残留的限定词（`小/中/大/十二/多用`）单独映射
- 最后用正则兜底清掉残留 CJK，**并断言输出里 0 个中文字符**（见 §6 验收）
- 材质串统一规范化：`410+430SS` → `410 stainless steel + 430 stainless steel`，
  连字符要放在中文词翻译**之后**处理，否则 `沙比利木430SS` 会漏

---

## 2. 图片处理流水线

### 2.1 从 xlsx 里把内嵌图取出来

图不在单元格里，而在 `xl/media/`，位置信息在 `xl/drawings/drawing1.xml`：

```python
# 关系映射：rId -> ../media/imageN.png
rels = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels_xml))
# 锚点：每个图的 from(col,row)
for m in re.finditer(r"<xdr:(oneCellAnchor|twoCellAnchor)\b(.*?)</xdr:\1>", draw_xml, re.S):
    ...
```

**两个坑**：

1. **rels 的 Target 是 `../media/xxx.png`**（相对 `xl/drawings/`），
   判断时不能用 `startswith("media/")`，要用 `"media/" in target`，再取 `basename`。
2. **`<xdr:from>` 里 col 和 row 之间夹着 `<xdr:colOff>`**，所以 `.*?` 跨不过去：

```python
# ❌ 匹配不到（.*? 撞上 colOff 就停了）
r"<xdr:from>\s*<xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>"
# ✅ 用否定前瞻限制在 from 块内
r"<xdr:from>\s*<xdr:col>(\d+)</xdr:col>(?:(?!</xdr:from>).)*?<xdr:row>(\d+)</xdr:row>"
```

### 2.2 白底裁切：边界洪水填充

产品图背景是白/浅灰，直接取全图会让产品很小。用**从四边洪水填充**标记背景，
再取"非背景"像素的包围盒：

```python
def is_bg(px):                      # 只把"亮且近中性灰"当背景
    r, g, b = px[:3]
    return min(r,g,b) >= 100 and (max(r,g,b)-min(r,g,b)) <= 34 and max(r,g,b) >= 150
# 四边入队 → BFS；包围盒 = 未访问像素的范围
```

**判定保护**（防止裁切失败导致图变空白）：
裁切后若 `宽<24` 或 `高<24`，或面积 < 原图 2%，就放弃裁切用原图。
小图先缩到 700px 再算边界，速度快且不影响结果（最后按比例映射回原尺寸）。

### 2.3 输出三档 + 双格式

```
{id}-thumb.jpg  520×390   卡片缩略
{id}-card.jpg   900×675   详情页主图
{id}-full.jpg  1400×1050  灯箱放大（保留）
```

封面/横幅类另外出 `960/1440/1920/2560` 四档，**JPEG + WebP 双格式**：

```python
resized.save(jpg, "JPEG", quality=82, optimize=True, progressive=True)
resized.save(webp, "WEBP", quality=78, method=5)
```

实测同一张图 **WebP 110KB vs JPEG 249KB，省 56%**。

### 2.4 PIL 三个必设项

```python
Image.MAX_IMAGE_PIXELS = None                        # 12600×12600 会触发 DecompressionBombError
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
if im.mode != "RGB": im = im.convert("RGB")          # CMYK（印刷源）必须转 sRGB，否则网页偏色
```

### 2.5 缺失图的优雅降级

源表里 3 行（L64/L66/L99）本来就没有配图。做法：
1. 做一张品牌化 `no-photo.svg` 占位（不用破图图标）
2. `app.js` 里**捕获阶段**监听 `error` 事件，全局替换失败的 `img.src`
3. 产品名/规格照常显示，不隐藏卡片

```js
document.addEventListener('error', function (e) {
  var t = e.target;
  if (t && t.tagName === 'IMG' && t.src.indexOf('no-photo.svg') === -1) t.src = PLACEHOLDER;
}, true);   // ← 必须 true，否则捕获不到资源加载错误
```

---

## 3. 静态站架构

### 3.1 数据与渲染分离

- `data/catalog.json`（236KB，445 款）承载全部产品字段
- 列表页由 `catalog.js` 拉 JSON 后客户端渲染（搜索/筛选/排序/分页）
- **详情页预生成 445 个静态 HTML**（SEO 友好、可直接分享），再用 `product.js` 增强（相关商品、多语言规格表、价格换算）

### 3.2 四语 i18n

- **英文当基准字典**，其它语言缺失键自动回退英文
- 语言检测：`localStorage` → `navigator.languages` → 默认英文
- 应用方式：`data-i18n` / `data-i18n-placeholder` / `data-i18n-title` / `data-i18n-aria`
- 切换语言广播 `skit:lang` 事件，各模块自行重渲染

**踩坑：HTML 实体与 textContent**

```js
el.textContent = dict[key];   // ← 用 textContent 时，字典里必须写 & 而不是 &amp;
```
字典里写 `&amp;` 会**字面显示成 `&amp;`**。修法：字面量转义符号只用在 HTML 模板里，
字典里一律用**真实字符**。需要富文本（如 `<b>`）时单独走 `innerHTML` 并明确注释。

**踩坑：子页面相对路径**

`products/x.html` 里 `assets/css/style.css` 会解析成 `products/assets/...`。
统一用基址变量：

```html
<script>window.SKIT_BASE = "../";</script>   <!-- 必须在 app.js 之前 -->
```
```js
var BASE = typeof window.SKIT_BASE === 'string' ? window.SKIT_BASE : '';
function u(p) { return BASE + p; }
```

### 3.3 响应式图片用 `<picture>`

```html
<picture>
  <source type="image/webp" srcset="…-960.webp 960w, …-1440.webp 1440w, …" sizes="100vw">
  <img src="…-1440.jpg" width="1920" height="1080" fetchpriority="high" decoding="async">
</picture>
```

首屏图 `fetchpriority="high"`，其余 `loading="lazy"`。
**始终写 width/height**，避免布局跳动。

### 3.4 照片当背景的两种写法

| 场景 | 写法 |
|---|---|
| 普通区块背景 | `background-image` + 媒体查询切分辨率 |
| 需要精细控制/SEO | 绝对定位的 `<img>`/`<picture>` + `object-fit: cover` |

带文字的照片区块统一用**深色渐变遮罩**保证可读性：

```css
.photo-band { position: relative; isolation: isolate; color: #fff; }
.photo-band .photo-band-bg { position: absolute; inset: 0; z-index: -2; object-fit: cover; }
.photo-band::after { content:""; position:absolute; inset:0; z-index:-1;
  background: linear-gradient(100deg, rgba(8,15,23,.94) 0%, rgba(8,15,23,.83) 34%, rgba(8,15,23,.3) 100%); }
```

`isolation: isolate` 让负 z-index 不跑到页面底下。

---

## 4. GitHub Pages 发布（坑最多的一节）

### 4.1 仓库名决定 URL 路径 ⭐

| 仓库名 | 站点地址 |
|---|---|
| `<user>.github.io` | `https://<user>.github.io/` （根域名） |
| 其它任意名 | `https://<user>.github.io/<仓库名>/` |

**关键**：`/SKit.github.io/` 这一层是**仓库名，不是文件夹**。
Pages 从**仓库根目录**提供服务 —— 所以 `index.html` 必须在根目录。
把站点放在 `dist/` 子目录里会导致**全站 404**（这是我这次最大的返工）。

> 同时注意：组织可能有 `Terrorschiki.github.io` 仓库占用根域名（Jekyll 博客）。
> 此时根路径的 `/assets/...` 属于**博客**而非本项目，探测时会拿到别人的文件，别误判成缓存。

### 4.2 workflow 必须在仓库根 `.github/workflows/` ⭐

放在 `dist/.github/workflows/` 等于没放 —— **Actions 完全不识别**，
`actions/runs` 里只会看到旧的 legacy 构建，容易误以为"推送失败"。

### 4.3 两种 build_type

| build_type | 行为 |
|---|---|
| `legacy` | 用内置 Jekyll builder。可能"构建成功但全站 404" |
| `workflow` | 用你自己的 Actions 发布 artifact（推荐、可控） |

```bash
# 切换（需要 repo 权限的 token）
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/OWNER/REPO/pages \
  -d '{"build_type":"workflow"}'
```

### 4.4 标准发布 workflow

```yaml
name: Deploy static site to Pages
on:
  push: { branches: [main] }
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write          # ← deploy-pages 需要
concurrency:
  group: pages
  cancel-in-progress: false   # ← 别取消进行中的部署
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with: { path: . }
      - id: deployment
        uses: actions/deploy-pages@v4
```

### 4.5 API 直接开通 Pages（免点设置页）

```python
# 查询（未开通返回 404）
GET  /repos/{owner}/{repo}/pages
# 开通：source=main、根目录
POST /repos/{owner}/{repo}/pages     {"source":{"branch":"main","path":"/"},"build_type":"legacy"}
# 之后可切 workflow
PUT  /repos/{owner}/{repo}/pages     {"build_type":"workflow"}
# 看构建状态
GET  /repos/{owner}/{repo}/pages/builds
GET  /repos/{owner}/{repo}/actions/runs
```

### 4.6 判断账号是 User 还是 Organization

```python
GET /users/{name}   → 看返回里 "type" 字段（User / Organization / Bot）
GET /orgs/{name}    → 200 表示是组织
```
组织主页 404 ≠ 仓库不存在。**admin 权限在 `permissions.admin`，不在 `owner.site_admin`**。

### 4.7 大文件限制

- **>50MB**：push 成功但给出 LFS 警告
- **>100MB**：直接拒绝

本次 6 个源文件（最大 72.9MB）都低于硬限，push 通过但会告警。
超限时的办法：压缩源文件 / 只发布压缩版 / 用 Git LFS / 外链网盘。

### 4.8 鉴权

Git Credential Manager 的凭据可直接复用：

```python
p = subprocess.run(["git","credential","fill"],
                   input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True)
TOKEN = dict(l.split("=",1) for l in p.stdout.splitlines() if "=" in l)["password"]
```

Windows 可用 `cmdkey /list` 查看存储的账号。
**scope 决定能做什么**：`gist, repo, workflow` 能推代码、能改仓库级 Pages；
改**组织级**设置还需要 `admin:org`。

---

## 5. 发布脚本的安全铁律 ⭐⭐

**我犯的严重错误**：`deploy.py` 里"清理陈旧文件"的逻辑是
"删除根目录下我不认识的东西" —— 结果**删掉了用户的原始报价单和 12 张原图**。

### 正确姿势：白名单 + 正身份判断

```python
# ❌ 危险：删除一切不在保留名单里的东西
for name in os.listdir(ROOT):
    if name in KEEP_TOP: continue
    shutil.rmtree(os.path.join(ROOT, name))     # ← 源文件、素材、笔记全没了

# ✅ 安全：只删"我本次确实会重新生成"的东西
produced = set(PUBLISH_DIRS) | set(PUBLISH_FILES)      # 我发布的目录/文件
for name in os.listdir(ROOT):
    if name in KEEP_TOP: continue
    publishable = name in produced or os.path.exists(os.path.join(SITE, name))
    if not publishable: continue                        # ← 不认识就不碰
    if name in {".git", ".github", ".gitignore", "_build", "site"}: continue
    ...
```

### 五条铁律

1. **删除操作必须基于白名单**，不能基于"黑名单 + 兜底全删"
2. **源数据/素材目录必须显式排除**，并且在 `.gitignore` 里也排除
3. **删除前打印将删除的清单**，并在首次运行时人工确认
4. **发布产物与源数据物理分离**（本次源图放 `网站封面图片/`，
   产物放 `assets/img/cover/`，发布脚本只写后者）
5. **重要源文件先进 git**（本次原图从未提交，导致**永久丢失**）

> 血的教训：12600×12600 的原图因为既没进 git、又没进回收站，**无法恢复**。
> 只能从已处理的 2560px 图库重建。做任何批处理前，先 `git add` 一次源文件。

---

## 6. 验收与自查清单

### 6.1 数据完整性断言（构建时跑）

```python
assert all(p["code"].strip() for p in products)            # 每款都有货号
assert all(p["name_en"].strip() for p in products)         # 每款都有英文名
assert not any(re.search(r"[\u4e00-\u9fff]", p["name_en"]) for p in products)  # 英文名无中文残留
assert len({p["id"] for p in products}) == len(products)   # 无重复 ID
assert len(json.load(i18n_en)) == len(json.load(i18n_xx))  # 四语词典键数一致
```

### 6.2 产物完整性（发布时跑）

```python
# 每款产品的 thumb/card/full 三张图都在
# 每款产品的详情页都存在
# 清理无引用的孤儿图片（换过 ID 方案后必然产生）
```

**踩坑**：第一版用行号做 ID（`p-r10`），第二版改成货号（`p-m-p01`），
产生 **333 张孤儿图**（约 40MB）。发布脚本要主动清理孤儿文件。

### 6.3 线上验收（HTTP 探测）

```powershell
foreach ($u in @('/','/collections.html','/products/l-l01.html',
                 '/data/catalog.json','/assets/css/style.css','/sitemap.xml')) {
  # 不能只看状态码：要校验返回体里有预期内容
  # （CDN 可能把别人的文件/404 页面以 200 返回）
}
```

**踩坑**：探测根路径的 `/assets/css/style.css` 返回 200，但内容是 **normalize.css**
（组织博客主题的样式表）。**状态码 200 不等于内容正确** —— 必须校验内容特征串。

### 6.4 动态渲染验收

用 Chrome headless dump DOM，检查 JS 真的渲染出来了：

```bash
chrome --headless=new --virtual-time-budget=15000 --dump-dom URL
```
```powershell
([regex]::Matches($dom,'class="prod-card"')).Count      # 应为每页 48
[regex]::Match($dom,'id="resultCount"[^>]*>(.{0,90})')  # 结果计数文案
```

**踩坑**：PowerShell 管道读 headless 输出会拿到**旧的缓冲内容**，
导致误判"线上没更新"。要先 `Out-File` 落盘再读。

### 6.5 横向溢出诊断（移动端）

注入临时脚本，列出所有超出视口宽度的元素：

```js
document.querySelectorAll('body *').forEach(el => {
  const r = el.getBoundingClientRect();
  if (r.width > vw + 1 || r.right > vw + 1) console.log(el.tagName, el.className, r.width, r.right);
});
```

**注意**：Chrome headless 有**最小窗口宽度约 497px**，
`--window-size=430` 得到的仍是 497px 视口 —— 截图看起来"右侧被切"是假象，
要另外用 `documentElement.scrollWidth === clientWidth` 判断真实溢出。

---

## 7. 环境坑（Windows）

### 7.1 PowerShell 引号地狱

在 `pwsh -Command` 里处理含引号/反斜杠/中文的字符串极易被解析器吃掉。
**对策：凡是复杂逻辑一律写 `.py` 或 `.ps1` 文件再执行**，不要用内联 here-string。

### 7.2 schannel TLS 失败

```
schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030e)
```
改用 OpenSSL 后端并指定 CA bundle：

```bash
git -c http.sslBackend=openssl \
    -c http.sslCAInfo="C:/Program Files/Git/mingw64/etc/ssl/certs/ca-bundle.crt" ls-remote URL
```

另外 git 可能配置了本机代理（`git config --global http.proxy`），
代理没启动时所有网络操作都会失败 —— 先确认代理进程在跑。

### 7.3 端口被旧进程占用

改了 serving 目录后仍 404？检查是否**有两个 python 进程抢同一端口**
（旧的还绑着已删除的 `dist/`）：

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId, CommandLine
```

---

## 8. 可复用脚本清单

| 脚本 | 职责 |
|---|---|
| `_build/extract.py` | 导出 xlsx 原始单元格 + 图片锚点，便于摸结构 |
| `_build/naming.py` | 货号解析、中英品名、材质规范化（**纯函数，便于单测**） |
| `_build/build_catalog.py` | 生成 `catalog.json` + 处理全部产品图（支持 `--force` / `--limit=N`） |
| `_build/build_covers.py` | 封面大图 → 多档 JPEG/WebP |
| `_build/build_pages.py` | 生成全部 HTML + sitemap + robots（含 i18n 模板） |
| `_build/deploy.py` | 安全发布到仓库根目录 + 完整性校验 + 清理孤儿 |
| `_build/check_pages.py` | 轮询 Pages 构建状态 |
| `_build/watch_deploy.py` | 监听 Actions + 探测线上 |
| `_build/diagnose_pages.py` | 404 归因（配置/构建/内容） |

**设计要点**：解析逻辑（`naming.py`）与 I/O 逻辑分离，
所有构建脚本可重复执行（幂等：图存在就跳过，`--force` 才重做）。

---

## 9. 一句话总结

| 教训 | 一句话 |
|---|---|
| 最大的坑 | **仓库名会在 URL 里出现，Pages 从仓库根提供服务** —— 站点别放子目录 |
| 最危险的代码 | **"删除不认识的文件"** —— 永远用白名单，永远先备份 |
| 最容易误判 | **HTTP 200 ≠ 内容正确** —— 校验内容特征串，不只看状态码 |
| 最容易漏 | **`.github/workflows/` 必须在根目录**，`build_type` 要设对 |
| 最省时间 | 正则/解析写完**立刻跑全量样本**，别等端到端 |
| 最稳的架构 | 解析（纯函数）↔ 构建（幂等）↔ 发布（白名单）三层分离 |
