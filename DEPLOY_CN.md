# 武理新生指南 - 国内部署指南

## 问题说明

本项目原部署在 GitHub Pages (`*.github.io`)，但该域名在国内存在严重的 DNS 污染和连接不稳定问题，导致无梯子环境下无法直接访问。

## 推荐方案：Cloudflare Pages

### 为什么选 Cloudflare Pages？

| 对比项 | GitHub Pages | Vercel | **Cloudflare Pages** |
|--------|-------------|--------|---------------------|
| 国内可访问性 | ★☆☆☆☆ | ★★★☆☆ | **★★★★★** |
| 免费额度 | 100GB/月 | 100GB/月 | **无限流量** |
| 自动部署 | 支持 | 支持 | **支持** |
| 中国 CDN | 无 | 无 | **京东云节点** |

Cloudflare 通过与京东云合作，在中国大陆设有 CDN 节点，是目前免费静态托管中国内访问最稳定的方案。

---

## 部署步骤

### 方案一：通过 GitHub Actions 自动部署（推荐）

#### 1. 注册 Cloudflare 账号
1. 访问 https://dash.cloudflare.com/sign-up
2. 使用邮箱注册（支持国内邮箱）
3. 验证邮箱完成注册

#### 2. 获取 API Token
1. 登录 Cloudflare Dashboard
2. 点击右上角头像 → **My Profile** → **API Tokens**
3. 点击 **Create Token**
4. 选择模板 **Cloudflare Pages: Edit**
5. 点击 **Continue to summary** → **Create Token**
6. **复制并保存生成的 Token**（只显示一次）

#### 3. 获取 Account ID
1. 在 Cloudflare Dashboard 右侧栏可以看到 **Account ID**
2. 或者访问：https://dash.cloudflare.com → 选择任意域名 → 右侧栏复制 Account ID
3. **复制并保存 Account ID**

#### 4. 配置 GitHub Secrets
1. 进入 GitHub 仓库：`https://github.com/zhw070129-alt/lxxzhwut`
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，添加以下两个：
   - **Name**: `CLOUDFLARE_API_TOKEN`，**Secret**: 粘贴步骤2的 Token
   - **Name**: `CLOUDFLARE_ACCOUNT_ID`，**Secret**: 粘贴步骤3的 Account ID

#### 5. 触发部署
```bash
git add .
git commit -m "添加 Cloudflare Pages 部署配置"
git push origin main
```
推送后，GitHub Actions 会自动触发 Cloudflare Pages 部署。

部署完成后，访问地址为：**https://wut-navigator.pages.dev**

---

### 方案二：通过 Cloudflare 控制台直接部署

如果你不想配置 GitHub Actions，也可以直接在 Cloudflare 控制台操作：

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单选择 **Workers & Pages**
3. 点击 **Create** → **Pages** → **Upload assets**
4. 项目名称填：`wut-navigator`
5. 上传整个项目文件夹（主要是 `index.html` 和 `images/` 文件夹）
6. 点击 **Deploy**

部署完成后，访问地址为：**https://wut-navigator.pages.dev**

---

### 方案三：使用 Wrangler CLI 部署（开发者）

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署项目
wrangler pages deploy . --project-name=wut-navigator
```

---

## 国内可访问性测试

部署完成后，可在无梯子环境下测试：

1. **直接访问**: https://wut-navigator.pages.dev
2. **测试页面**: https://wut-navigator.pages.dev/connectivity-test.html
3. **ping 测试**: `ping wut-navigator.pages.dev`

如果 `pages.dev` 域名在国内仍不稳定，可以绑定自定义域名（见下文）。

---

## 绑定自定义域名（可选，推荐）

自定义域名可以进一步提升国内访问稳定性：

### 1. 购买域名
推荐使用国内域名服务商（已实名认证）：
- 阿里云万网：https://wanwang.aliyun.com
- 腾讯云 DNSPod：https://dnspod.cloud.tencent.com
- 华为云域名：https://www.huaweicloud.com/product/domain.html

建议选择 `.cn` 或 `.com` 域名（国内解析更稳定）。

### 2. 在 Cloudflare 绑定域名
1. 登录 Cloudflare Dashboard → 选择 `wut-navigator` 项目
2. 点击 **Custom domains** → **Set up a custom domain**
3. 输入你的域名（如 `wut.zuohaowen.com`）
4. Cloudflare 会提示你修改 DNS 服务器

### 3. 修改 DNS 服务器（在域名服务商处操作）
将域名的 DNS 服务器修改为 Cloudflare 提供的地址：
```
xxx.ns.cloudflare.com
yyy.ns.cloudflare.com
```
修改后等待 24-48 小时生效（通常几小时即可）。

### 4. 验证域名绑定
DNS 生效后，Cloudflare 会自动：
- 为你的域名配置 SSL 证书（免费）
- 启用中国区 CDN 加速
- 通过京东云节点提供国内访问

---

## 保留原有访问方式

本项目的 GitHub Pages 仍然保留作为备份：
- GitHub Pages: https://zhw070129-alt.github.io/lxxzhwut
- Cloudflare Pages: https://wut-navigator.pages.dev

可以在网页中添加访问引导，提示用户优先使用 Cloudflare 地址。

---

## 常见问题

### Q: Cloudflare Pages 国内真的能访问吗？
A: 是的。Cloudflare 通过与京东云合作在中国大陆有 CDN 节点，对于静态页面访问性非常好。如果你绑定的是已备案的国内域名，访问性更佳。

### Q: 需要 ICP 备案吗？
A: 使用 `pages.dev` 免费域名不需要备案。如果绑定自己的域名，绑定在 Cloudflare（境外 DNS）上通常也不需要备案，但如果使用国内 CDN 服务可能需要。

### Q: 流量有限制吗？
A: Cloudflare Pages 免费版无流量限制（unlimited bandwidth），适合大流量访问。

### Q: 部署后发现 `pages.dev` 在国内也不稳定？
A: 如果遇到这种情况，建议：
1. 绑定自定义域名（步骤见上文）
2. 或切换到国内云服务方案（阿里云 OSS + CDN）

---

## 替代方案：阿里云 OSS + CDN（最稳定但需实名）

如果 Cloudflare Pages 仍不能满足稳定性要求，可使用阿里云 OSS：

### 优势
- CDN 节点全部在国内，访问速度最快
- 阿里云新用户有免费额度
- 支持自定义域名和 HTTPS

### 步骤概要
1. 注册阿里云账号并实名认证
2. 创建 OSS Bucket（地域选武汉）
3. 开启静态网站托管
4. 上传 `index.html` 和 `images/` 文件夹
5. （可选）绑定自定义域名 + 开启 CDN 加速

费用参考：OSS 存储约 ¥0.12/GB/月，CDN 流量约 ¥0.24/GB（新用户有大量免费额度）。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `.github/workflows/cloudflare-pages.yml` | Cloudflare Pages 自动部署工作流 |
| `.github/workflows/deploy.yml` | GitHub Pages 部署工作流（保留作为备份） |
| `wrangler.toml` | Wrangler CLI 配置文件 |
| `connectivity-test.html` | 国内可访问性测试页面 |
| `DEPLOY_CN.md` | 本部署指南 |
