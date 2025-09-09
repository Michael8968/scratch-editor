# Microbit 下载问题解决方案

## 问题描述

在运行 `npm install` 时遇到以下错误：
```
npm error TypeError: fetch failed
npm error [cause]: Error: read ECONNRESET
```

这个错误是由于网络连接问题导致无法从 `https://downloads.scratch.mit.edu/microbit/scratch-microbit.hex.zip` 下载 microbit hex 文件。

## 解决方案

### 方案1：自动重试（推荐）

我们已经修改了 `packages/scratch-gui/scripts/prepare.mjs` 脚本，添加了以下功能：

- **重试机制**：最多重试3次
- **指数退避**：重试间隔为2秒、4秒、8秒
- **超时设置**：30秒下载超时
- **更好的错误信息**：提供详细的错误信息和手动解决方案

现在可以直接重新运行：
```bash
npm install
```

### 方案2：手动下载

如果自动重试仍然失败，可以使用我们提供的手动下载脚本：

```bash
# 在 scratch-editor 根目录运行
./scripts/manual-microbit-download.sh
```

这个脚本会：
1. 下载 microbit hex 文件
2. 解压到正确的位置
3. 生成必要的 require 文件
4. 清理临时文件

### 方案3：完全手动操作

如果脚本也无法运行，可以完全手动操作：

1. **下载文件**：
   - 访问：https://downloads.scratch.mit.edu/microbit/scratch-microbit.hex.zip
   - 下载到本地

2. **解压文件**：
   ```bash
   unzip scratch-microbit.hex.zip
   ```

3. **复制文件**：
   ```bash
   mkdir -p packages/scratch-gui/static/microbit
   cp *.hex packages/scratch-gui/static/microbit/
   ```

4. **生成 require 文件**：
   ```bash
   mkdir -p packages/scratch-gui/src/generated
   echo "module.exports = require('./static/microbit/scratch-microbit.hex');" > packages/scratch-gui/src/generated/microbit-hex-url.cjs
   ```

## 验证安装

完成上述任一方案后，重新运行：
```bash
npm install
```

如果成功，你应该看到类似以下的输出：
```
> scratch-gui@1.0.0 prepare
> node scripts/prepare.mjs
Download successful on attempt 1
Found matching file: scratch-microbit.hex
Extracting static/microbit/scratch-microbit.hex
Wrote src/generated/microbit-hex-url.cjs
Prepare script complete
```

## 常见问题

### Q: 为什么会出现这个错误？
A: 这通常是由于网络不稳定、防火墙设置或服务器临时不可用导致的。

### Q: 修改后的脚本是否安全？
A: 是的，我们只添加了重试机制和更好的错误处理，没有改变核心功能。

### Q: 如果手动下载后仍然失败怎么办？
A: 请检查：
- 网络连接是否正常
- 防火墙设置是否阻止了下载
- 是否有代理服务器配置问题

## 技术细节

修改的文件：
- `packages/scratch-gui/scripts/prepare.mjs` - 添加重试机制
- `scripts/manual-microbit-download.sh` - 手动下载脚本（新增）

这些修改确保了在网络不稳定的情况下，构建过程能够更加可靠地完成。
