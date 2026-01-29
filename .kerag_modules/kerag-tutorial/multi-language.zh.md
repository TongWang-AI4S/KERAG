# 多语言支持 [@multi-language]

KERAG 支持多语言知识库，允许你为同一内容提供不同语言版本，并根据用户的语言偏好自动选择最合适的版本。

## 文件命名约定 [@file-naming]

多语言文件通过后缀标识语言版本：

- **默认语言文件**: `filename.md` 或 `index.md`
- **中文版本**: `filename.zh.md` 或 `index.zh.md`
- **英文版本**: `filename.en.md` 或 `index.en.md`
- **其他语言**: 使用 ISO 639-1 两位语言代码（如 `.ja` 日语、`.de` 德语等）

**目录结构示例**:
```text
linear-algebra/
├── index.md           # 默认版本
├── index.zh.md        # 中文版入口
├── index.en.md        # 英文版入口
├── matrix.md          # 默认版本
├── matrix.zh.md       # 中文版矩阵章节
└── matrix.en.md       # 英文版矩阵章节
```

## 语言解析优先级 [@language-priority]

当系统需要查找某个 `file_id` 对应的物理文件时，会按照以下优先级顺序尝试：

假设当前语言设置为 `zh`，查找 `linear-algebra/matrix`：

1. `linear-algebra/matrix.zh.md` （优先匹配当前语言）
2. `linear-algebra/matrix.md` （回退到默认版本）

对于目录类型的引用（如 `linear-algebra`）：

1. `linear-algebra/index.zh.md` （优先匹配当前语言）
2. `linear-algebra/index.md` （回退到默认版本）

## 文件 ID 与语言无关性 [@file-id-language]

**重要**: 无论使用哪种语言版本，文件 ID 都是相同的。

- `matrix.zh.md` 和 `matrix.en.md` 的文件 ID 都是 `linear-algebra::matrix`
- 引用时无需指定语言：`(@linear-algebra/matrix::content)` 会自动解析为当前语言的版本

这种设计确保了跨语言引用的简洁性和一致性。

## 配置语言偏好 [@language-config]

系统通过以下方式确定当前语言：

- **环境变量**: 设置 `KERAG_LANG` 环境变量（如 `zh`, `en`）
- **程序接口**: 在代码中调用时传入 `lang` 参数

```bash
# 设置环境变量后运行命令
export KERAG_LANG=zh
```

## 最佳实践 [@best-practices-i18n]

### 结构一致性
不同语言版本的文件应该保持相同的章节结构和标签命名，确保跨语言引用能够正确解析：

```markdown
<!-- matrix.zh.md -->
# 矩阵 [@matrix]
矩阵是一个按照长方阵列排列的复数或实数集合。

<!-- matrix.en.md -->
# Matrix [@matrix]
A matrix is a rectangular array of complex or real numbers.
```

### 默认语言回退
建议始终提供默认语言版本（不带语言后缀的文件），这样当某个语言版本缺失时，系统可以优雅地回退到默认版本，而不是报错。
