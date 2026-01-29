# 模块管理、打包与安装 [@module-management]

## 模块扫描与本地管理 (Scan) [@module-scan]

当你在本地创建或修改了模块，运行扫描命令来更新本地注册信息：

```bash
kerag scan
```

此命令会执行以下操作：
1. 遍历局部与全局知识根目录（默认为`workdir/.kerag_modules`与`~/.kerag_modules/`，可以通过环境变量`KERAG_LOCAL`与`KERAG_HOME`指定）寻找包含 `index.md` 的文件夹。
2. 从`index.md`中解析模块元数据。
3. 生成或更新 `.kerag_modules/modules.yml` 索引文件

## 模块打包 (Pack) [@module-pack]

为了分发你的知识库，你可以使用打包工具将其转换为标准的 `.tar` 归档文件。

**命令格式**:
```bash
kerag tool pack [模块目录] [-o 输出文件名] [--name 模块名] [--version 版本] [--description 描述]
```

**关键特性**:
- **元数据一致性检查**: 打包工具会严格检查 `index.md`、`--meta` 文件以及命令行参数提供的信息。如果这三者之间存在相互矛盾的定义（如不同的版本号），工具会报错并停止打包。
- **自动生成元数据**: 打包过程会自动在归档文件根目录生成 `kerag_meta.txt`。
- **结构优化**: 打包后的文件结构经过优化，确保解压后能直接被 KERAG 识别和安装。

**案例演示**:
```bash
# 将 linear-algebra 目录打包，显式指定版本和名称
kerag tool pack ./linear-algebra --name linear-algebra-example --version 1.0.0 -o la-v1.tar
```

## 安装外部模块 (Install) [@module-install]

除了在 KERAG 知识路径中自动扫描，你也可以在任何路径下准备好符合规范的模块目录，然后通过 `install` 命令将其安装到 KERAG 系统中。

### 模块目录规范

为了确保 `kerag install` 能正确识别模块，源目录或压缩文件（`.tar`, `.zip`等）必须符合以下结构之一：
1. **单文件夹结构**: 根目录下仅包含一个文件夹，且该文件夹内包含 `index.md`。
2. **显式元数据结构**: 根目录下包含多个文件/文件夹，但必须有一个 `kerag_meta.txt` 文件。该文件的第一行必须指明包含 `index.md` 的实际模块目录名。

**注意**: 使用 `kerag tool pack` 生成的 `.tar` 文件正是严格遵循上述"显式元数据结构"生成的。在进行打包时，应该将目标路径指定为**模块目录本身**（即包含 `index.md` 的那个目录），而不是它的父目录。

### 来源类型

- **Git 仓库**: 使用 `git+` 前缀。
- **远程归档 (HTTP/HTTPS)**: 直接指向归档文件的 URL。支持 `.tar`, `.tar.gz`, `.zip` 格式。
- **本地目录或归档文件**: 本地磁盘路径。

**案例演示 (从远程服务器下载并安装 tar 包)**:
```bash
# 安装一个示例线性代数模块
kerag install https://raw.githubusercontent.com/TongWang-AI4S/KERAG-Modules/refs/heads/main/the-first-example-0.0.tar
```

**输出示例**:
```text
Downloading module from https://raw.githubusercontent.com/TongWang-AI4S/KERAG-Modules/refs/heads/main/the-first-example-0.0.tar...
Extracting TAR archive...
Successfully installed module: the-first-example
```

**其它安装示例**:
```bash
# 从 Git 仓库安装
kerag install git+https://github.com/username/kerag-physics.git

# 从本地目录安装
kerag install ./my-custom-module-dir

# 强制覆盖已安装的模块 (-f)
kerag install ./module-v2.tar -f
```
