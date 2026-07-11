#!/usr/bin/env python3
"""
企业微信配置检查脚本
检查配置是否正确，并测试企业微信API连通性
"""
import sys, json, os, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_config():
    """交互式配置检查"""
    print("=" * 55)
    print("  🔍 企业微信接入检查工具")
    print("=" * 55)
    
    corp_id = input("\n1️⃣  企业ID（CorpID）：").strip()
    agent_id = input("2️⃣  应用AgentId：").strip()
    secret = input("3️⃣  应用Secret：").strip()
    
    if not all([corp_id, agent_id, secret]):
        print("\n❌ 三项必填，请重新运行")
        return
    
    print("\n⏳ 正在验证...")
    
    # 测试获取token
    resp = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        params={"corpid": corp_id, "corpsecret": secret},
        timeout=10
    )
    data = resp.json()
    
    if data.get("errcode") != 0:
        print(f"\n❌ 验证失败：{data.get('errmsg', '未知错误')}")
        print("  可能原因：")
        print("  - CorpID 不正确（后台→我的企业→企业信息）")
        print("  - Secret 不正确（应用管理→自建应用→Secret）")
        return
    
    token = data["access_token"]
    print("✅ Token获取成功！")
    
    # 测试获取应用信息
    resp2 = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/agent/get",
        params={"access_token": token, "agentid": agent_id},
        timeout=10
    )
    agent_data = resp2.json()
    
    if agent_data.get("errcode") == 0:
        print(f"✅ 应用验证通过：{agent_data.get('name', '')}")
        print(f"   应用类型：{'自建' if agent_data.get('close', 0) == 0 else '已停用'}")
    else:
        print(f"⚠️  AgentId 可能不正确：{agent_data.get('errmsg','')}")
    
    # 生成配置文件
    config = {
        "CORP_ID": corp_id,
        "AGENT_ID": agent_id,
        "SECRET": secret,
        "TOKEN": "xuefengren2026",
        "ENCODING_AES_KEY": ""
    }
    
    config_path = "/workspace/SCRIPTS/wecom_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 配置文件已保存：{config_path}")
    print(f"   启动方式：python3 wecom_bot.py --config {config_path}")
    
    # 生成配置指引
    print(f"""
╔══════════════════════════════════════════════════╗
║              下一步配置步骤                       ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  1. 确保服务在公网可达的服务器上运行               ║
║                                                  ║
║  2. 登录企业微信后台 → 应用管理 → 自建应用        ║
║     填入接收消息服务器配置：                      ║
║     URL: https://你的域名/wecom/callback        ║
║     Token: xuefengren2026                       ║
║     EncodingAESKey: 随机生成                     ║
║                                                  ║
║  3. 在企业微信App中打开该应用即可开始对话          ║
║     也可配置到工作台让全员使用                    ║
║                                                  ║
║  4. 发送「开始」→ 16步评估 → PDF报告图片          ║
║     发送「报告」→ 查看已有分析报告                ║
║     直接输入→ AI对话                             ║
║                                                  ║
╚══════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    check_config()
