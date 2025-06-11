# milvus-binary-verify

一个用于 **验证 Milvus DEB/RPM 安装包** 能否正确安装并成功连接到 Milvus 服务的脚本集合。

## 目录结构

| 路径 | 说明 |
| ---- | ---- |
| `verify-package.sh` | 主验证脚本：安装包、检查二进制、创建虚拟环境并执行 Python 示例 |
| `hello_milvus.py`   | Python 示例代码：向 Milvus 插入并查询数据 |
| `requirements.txt`  | Python 依赖列表 |

## 前置条件

1. Linux x86_64 系统，且拥有 **sudo** 权限用于安装包。
2. 已安装 `bash`、`curl`、`python3 (>=3.8)`。其余依赖会由脚本自动安装：
   - **uv**：用于创建虚拟环境和安装 Python 依赖
   - 系统包管理工具：`apt-get` / `yum` / `dnf`

## 快速开始

```bash
# 克隆代码仓库（如已在包同级目录可跳过）
git clone https://github.com/xx/milvus-binary-verify.git
cd milvus-binary-verify

# 赋予脚本执行权限（仅首次需要）
chmod +x verify-package.sh

# 执行验证
./verify-package.sh <package-path> <binary-name>
```

常见示例：

```bash
# 以 RPM 包为例
./verify-package.sh milvus-2.4.0-20250611.x86_64.rpm milvus

# 以 DEB 包为例
./verify-package.sh milvus_2.4.0-20250611_amd64.deb milvus
```

> **提示**：脚本会在当前目录下创建 `.venv` 虚拟环境，并在失败时将 Milvus 状态与日志收集到 `milvus-debug-logs/` 目录，便于排查。

## 脚本参数说明

| 参数 | 必选 | 说明 |
| ---- | ---- | ---- |
| `package-path` | 是 | `.deb` 或 `.rpm` 包的绝对/相对路径 |
| `binary-name`  | 是 | 安装成功后应出现在 `$PATH` 中的主可执行文件名（如 `milvus`） |

## 运行结果判定

- **成功**：脚本输出 `hello_milvus validation completed successfully.` 并以状态码 `0` 结束。
- **失败**：脚本输出错误信息并以非零状态码结束，排查步骤见下文。

## 故障排查

1. **依赖缺失**：
   - 若安装包依赖未满足，脚本会尝试 `apt-get -f install` / `yum localinstall` 自动补全；如仍失败，请手动检查依赖。
2. **二进制缺失**：确认 `binary-name` 是否填写正确，以及包内是否包含对应可执行文件。
3. **Python 示例失败**：脚本会自动收集 Milvus 服务状态与最近 200 行日志至 `milvus-debug-logs/`，请首先查看 `status.txt` 与 `journal.txt`。

## hello_milvus.py 手动执行

如需单独运行示例，可先激活已有虚拟环境：

```bash
source .venv/bin/activate
python hello_milvus.py --host 127.0.0.1 --port 19530
```

默认参数：

```text
--host 127.0.0.1   # Milvus 服务地址
--port 19530       # Milvus gRPC 端口
```

## 贡献

欢迎提交 Issue 或 PR 以改进脚本及文档。

## 许可证

MIT License