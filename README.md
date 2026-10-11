# DeepSeek 余额 MCP 插件

极简 MCP 服务器，只做一个工具：`get_balance`（查 DeepSeek 余额）。
**自动读取 Operit 已配置的 DeepSeek API Key，导入即用，无需任何输入。**

## 文件
- deepseek_balance.py  # MCP 服务器（纯标准库，无需 pip）

## 导入 Operit
1. Operit → 设置 → MCP / 插件 → 添加 MCP 服务器（stdio 类型）
2. 命令：`python3`
   参数：`/storage/emulated/0/Download/Operit/mcp/deepseek_balance.py`
3. 保存并启用

## 使用
直接让助手「查 DeepSeek 余额」即可。

## Key 来源（按优先级）
1. 环境变量 DEEPSEEK_API_KEY
2. 本目录 config.json 的 api_key（可选，显式覆盖）
3. **自动读取 Operit 配置**：
   /data/data/com.ai.assistance.operit/files/datastore/model_configs.preferences_pb
   （从中解析 apiKey 字段，无需手动填写）
