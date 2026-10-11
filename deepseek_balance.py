
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极简 MCP 服务器：查询 DeepSeek 余额。仅用标准库。
导入方式（Operit 里添加 MCP）：
  命令: python3
  参数: /storage/emulated/0/Download/Operit/mcp/deepseek_balance.py
API Key 来源优先级：环境变量 DEEPSEEK_API_KEY > 同目录 config.json 的 api_key
"""
import sys, json, os, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.deepseek.com/user/balance"

def get_key_from_operit():
    """从 Operit 的 model_configs.preferences_pb 自动读取 DeepSeek apiKey。
    Operit 配置路径：/data/data/com.ai.assistance.operit/files/datastore/
    需要 root/可读权限（linux proot 终端下一般可读）。"""
    import re, glob
    candidates = [
        "/data/data/com.ai.assistance.operit/files/datastore/model_configs.preferences_pb",
        "/sdcard/Android/data/com.ai.assistance.operit/files/datastore/model_configs.preferences_pb",
    ]
    for p in candidates:
        if not os.path.exists(p):
            continue
        try:
            raw = open(p, "rb").read().decode("utf-8", "ignore")
        except Exception:
            continue
        # 找形如 "apiKey":"sk-xxx" 的字段（可能带转义）
        for m in re.finditer(r'apiKey\\?"\s*:\s*\\?"(sk-[A-Za-z0-9_\-]+)', raw):
            return m.group(1)
        # 兜底：任意 sk- 开头的串
        m2 = re.search(r'(sk-[A-Za-z0-9_\-]{16,})', raw)
        if m2:
            return m2.group(1)
    return ""

def get_key():
    k = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if k:
        return k
    # 先读插件自己的 config.json（用户显式指定优先）
    cfg = os.path.join(HERE, "config.json")
    if os.path.exists(cfg):
        try:
            k = json.load(open(cfg, encoding="utf-8")).get("api_key", "").strip()
            if k and not k.startswith("sk-在这里"):
                return k
        except Exception:
            pass
    # 再自动读取 Operit 配置
    return get_key_from_operit()

def save_key(k):
    try:
        json.dump({"api_key": k}, open(os.path.join(HERE, "config.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass

def query_balance(new_key=None):
    if new_key:
        new_key = new_key.strip()
        if new_key:
            save_key(new_key)
            key = new_key
        else:
            key = get_key()
    else:
        key = get_key()
    if not key:
        return ("尚未设置 API Key。\n"
                "请在对话中把 Key 交给助手，调用 get_balance 时带上 api_key 参数，"
                "例如：get_balance(api_key=\"sk-xxxx\")，设置后会自动保存，下次无需再填。\n"
                "也可直接编辑 config.json 的 api_key 字段。")
    req = urllib.request.Request(API, headers={
        "Authorization": "Bearer " + key.encode("ascii", "ignore").decode("ascii"),
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")[:300]
        if e.code == 401:
            return "API Key 无效或已过期（HTTP 401）。请重新提供正确的 Key。\n%s" % msg
        return "请求失败 HTTP %s：%s" % (e.code, msg)
    except Exception as e:
        return "请求异常：%s" % e

    lines = []
    for b in data.get("balance_infos", []):
        lines.append("货币 %s｜总余额 %s｜赠送 %s｜充值 %s" % (
            b.get("currency"), b.get("total_balance"),
            b.get("granted_balance"), b.get("topped_up_balance")))
    head = "可用" if data.get("is_available") else "不可用"
    return "DeepSeek 账户状态：%s\n%s" % (head, "\n".join(lines) if lines else "(无余额信息)")

TOOLS = [{
    "name": "get_balance",
    "description": "查询 DeepSeek 账户余额（货币、总余额、赠送、充值）。首次使用需提供 api_key，之后自动保存。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "DeepSeek API Key（形如 sk-xxx）。首次/Key失效时提供，会自动保存；已保存过则可省略。"
            }
        },
        "required": []
    },
}]

def send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def handle(msg):
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "deepseek-balance", "version": "1.0.0"}}})
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        if name == "get_balance":
            args = params.get("arguments") or {}
            text = query_balance(args.get("api_key"))
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": text}]}})
        else:
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": "未知工具: %s" % name}],
                "isError": True}})
    elif mid is not None:
        send({"jsonrpc": "2.0", "id": mid, "result": {}})

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
