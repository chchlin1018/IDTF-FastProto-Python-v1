# Git 分支策略

本文件定義 IDTF FastProto 專案的 Git 分支策略和工作流程。

---

## 分支結構

### 主要分支

#### `main`
**生產環境分支**

- 包含生產環境的穩定代碼
- 只接受來自 `release/*` 分支的合併
- 每次合併到 `main` 都應該打上版本標籤（如 `v1.0.0`）
- 受保護分支，需要 Pull Request 和代碼審查

**保護規則**:
- 禁止直接推送
- 需要至少 1 個審查批准
- 需要通過所有 CI 檢查

#### `develop`
**開發分支**

- 包含最新的開發代碼
- 所有功能分支的合併目標
- 定期合併到 `release/*` 分支進行發布準備
- 受保護分支，需要 Pull Request

**保護規則**:
- 禁止直接推送
- 需要通過所有 CI 檢查

---

### 支援分支

#### `feature/*`
**功能開發分支**

從 `develop` 分支創建，開發完成後合併回 `develop`。

**命名規範**:
- `feature/<功能名稱>`
- 例如：`feature/iadl-parser`, `feature/collision-detection`

**工作流程**:
```bash
# 從 develop 創建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/iadl-parser

# 開發功能
# ... 進行開發和提交 ...

# 推送到遠端
git push origin feature/iadl-parser

# 創建 Pull Request 到 develop
# ... 在 GitHub 上創建 PR ...

# 合併後刪除分支
git checkout develop
git pull origin develop
git branch -d feature/iadl-parser
```

#### `bugfix/*`
**Bug 修復分支**

從 `develop` 分支創建，修復完成後合併回 `develop`。

**命名規範**:
- `bugfix/<bug描述>`
- 例如：`bugfix/tag-position-calculation`, `bugfix/usd-import-error`

**工作流程**:
```bash
# 從 develop 創建 bugfix 分支
git checkout develop
git pull origin develop
git checkout -b bugfix/tag-position-calculation

# 修復 bug
# ... 進行修復和提交 ...

# 推送到遠端
git push origin bugfix/tag-position-calculation

# 創建 Pull Request 到 develop
# ... 在 GitHub 上創建 PR ...

# 合併後刪除分支
git checkout develop
git pull origin develop
git branch -d bugfix/tag-position-calculation
```

#### `release/*`
**發布準備分支**

從 `develop` 分支創建，準備新版本發布。在此分支上進行版本號更新、文件更新和最後的 bug 修復。

**命名規範**:
- `release/v<版本號>`
- 例如：`release/v0.1.0`, `release/v1.0.0`

**工作流程**:
```bash
# 從 develop 創建 release 分支
git checkout develop
git pull origin develop
git checkout -b release/v0.1.0

# 更新版本號
# ... 更新 __version__.py, CHANGELOG.md 等 ...

# 進行最後的 bug 修復和測試
# ... 進行修復和提交 ...

# 推送到遠端
git push origin release/v0.1.0

# 合併到 main
git checkout main
git pull origin main
git merge --no-ff release/v0.1.0
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin main --tags

# 合併回 develop
git checkout develop
git pull origin develop
git merge --no-ff release/v0.1.0
git push origin develop

# 刪除 release 分支
git branch -d release/v0.1.0
git push origin --delete release/v0.1.0
```

#### `hotfix/*`
**緊急修復分支**

從 `main` 分支創建，用於修復生產環境的緊急問題。修復完成後合併到 `main` 和 `develop`。

**命名規範**:
- `hotfix/<問題描述>`
- 例如：`hotfix/critical-crash`, `hotfix/security-vulnerability`

**工作流程**:
```bash
# 從 main 創建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-crash

# 修復問題
# ... 進行修復和提交 ...

# 更新版本號（patch 版本）
# ... 更新 __version__.py, CHANGELOG.md 等 ...

# 推送到遠端
git push origin hotfix/critical-crash

# 合併到 main
git checkout main
git pull origin main
git merge --no-ff hotfix/critical-crash
git tag -a v0.1.1 -m "Hotfix version 0.1.1"
git push origin main --tags

# 合併到 develop
git checkout develop
git pull origin develop
git merge --no-ff hotfix/critical-crash
git push origin develop

# 刪除 hotfix 分支
git branch -d hotfix/critical-crash
git push origin --delete hotfix/critical-crash
```

---

## 提交訊息規範

### 格式

```
<類型>(<範圍>): <簡短描述>

<詳細描述>（可選）

<footer>（可選）
```

### 類型

- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文件更新
- `style`: 代碼格式（不影響代碼運行的變動）
- `refactor`: 重構（既不是新增功能，也不是修復 bug 的代碼變動）
- `perf`: 性能優化
- `test`: 增加測試
- `chore`: 構建過程或輔助工具的變動

### 範例

```
feat(iadl): Add IADL v1.0 parser

Implement IADL v1.0 parser with support for:
- UUIDv7 asset_id and tag_id
- Tag attachment strategies (by-pos and by-prim)
- Validation rules for scaling constraints

Closes #123
```

```
fix(collision): Fix AABB collision detection bug

The AABB collision detection was incorrectly handling edge cases
where bounding boxes share a face. This fix ensures that touching
boxes are not considered colliding.

Fixes #456
```

---

## Pull Request 流程

### 1. 創建 Pull Request

在 GitHub 上創建 Pull Request，從功能分支到目標分支（通常是 `develop`）。

**PR 標題格式**:
```
<類型>: <簡短描述>
```

**PR 描述模板**:
```markdown
## 變更摘要
<!-- 簡要描述此 PR 的變更內容 -->

## 變更類型
- [ ] 新功能 (feature)
- [ ] Bug 修復 (bugfix)
- [ ] 文件更新 (docs)
- [ ] 重構 (refactor)
- [ ] 性能優化 (perf)
- [ ] 測試 (test)
- [ ] 其他 (chore)

## 測試
<!-- 描述如何測試此變更 -->

## 相關 Issue
<!-- 關聯的 Issue 編號，例如：Closes #123 -->

## 檢查清單
- [ ] 代碼遵循專案的代碼風格
- [ ] 已添加必要的測試
- [ ] 所有測試通過
- [ ] 已更新相關文件
- [ ] 沒有引入新的警告
```

### 2. 代碼審查

- 至少需要 1 個審查者批准
- 審查者應檢查：
  - 代碼質量和風格
  - 測試覆蓋率
  - 文件完整性
  - 潛在的性能問題
  - 安全性問題

### 3. CI 檢查

所有 PR 必須通過以下 CI 檢查：
- 代碼風格檢查（flake8, black）
- 單元測試（pytest）
- 類型檢查（mypy）
- 測試覆蓋率（至少 80%）

### 4. 合併

- 使用 "Squash and merge" 或 "Merge commit"（根據情況選擇）
- 合併後刪除功能分支

---

## 版本號規範

本專案遵循語義化版本號（Semantic Versioning）規範。

**格式**: `MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 變更
- **MINOR**: 向後兼容的功能新增
- **PATCH**: 向後兼容的 bug 修復

**範例**:
- `v0.1.0`: 初始 MVP 版本
- `v0.2.0`: 新增批量佈局功能
- `v0.2.1`: 修復碰撞檢測 bug
- `v1.0.0`: 第一個穩定版本

---

## 分支保護規則

### `main` 分支

- ✅ 需要 Pull Request
- ✅ 需要至少 1 個審查批准
- ✅ 需要通過所有 CI 檢查
- ✅ 禁止強制推送
- ✅ 禁止刪除

### `develop` 分支

- ✅ 需要 Pull Request
- ✅ 需要通過所有 CI 檢查
- ✅ 禁止強制推送
- ✅ 禁止刪除

---

## 常見問題

### Q: 如何同步 fork 的倉庫？

```bash
# 添加上游倉庫
git remote add upstream https://github.com/chchlin1018/IDTF-FastProto-Python-v1.git

# 獲取上游變更
git fetch upstream

# 合併到本地 develop
git checkout develop
git merge upstream/develop
git push origin develop
```

### Q: 如何解決合併衝突？

```bash
# 更新本地 develop
git checkout develop
git pull origin develop

# 切換到功能分支
git checkout feature/my-feature

# 合併 develop 到功能分支
git merge develop

# 解決衝突
# ... 手動編輯衝突文件 ...

# 標記為已解決
git add <衝突文件>
git commit -m "Resolve merge conflicts"

# 推送到遠端
git push origin feature/my-feature
```

### Q: 如何撤銷錯誤的提交？

```bash
# 撤銷最後一次提交（保留變更）
git reset --soft HEAD~1

# 撤銷最後一次提交（丟棄變更）
git reset --hard HEAD~1

# 如果已經推送，使用 revert
git revert HEAD
git push origin <branch-name>
```

---

## 參考資源

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

