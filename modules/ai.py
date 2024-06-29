import os
import json
import aiohttp
import aiofiles  # type: ignore
from datetime import datetime, timedelta
from pymongo import MongoClient

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

channel = Channel.current()

# API密钥
API_KEY = "sk-3YXHUIfKEJZvb9vg910a611666154dA18b455359303a412b"


# 异步调用ChatGPT API的函数
async def call_chatgpt_api(prompt, model):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.xiaoai.plus/v1/engines/{model}/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        data = {"prompt": prompt, "max_tokens": 150}
        async with session.post(url, headers=headers, json=data) as response:
            result = await response.json()
            return result.get("choices", [{}])[0].get("text", "")


# 异步记录对话历史的函数
async def save_conversation(user_id, conversation):
    user_dir = os.path.join("conversations", str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(user_dir, f"{timestamp}.json")

    async with aiofiles.open(file_path, "w") as f:
        await f.write(json.dumps(conversation, ensure_ascii=False, indent=4))


# 异步检查会话是否过期
async def is_session_expired(user_id):
    user_dir = os.path.join("conversations", str(user_id))
    if not os.path.exists(user_dir):
        return False, None

    files = sorted(os.listdir(user_dir))
    if not files:
        return False, None

    latest_file = files[-1]
    latest_timestamp = datetime.strptime(latest_file.split(".")[0], "%Y-%m-%d_%H-%M-%S")
    if datetime.now() - latest_timestamp > timedelta(weeks=1):
        return True, latest_timestamp
    return False, latest_timestamp


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def ai_help(
    app: Ariadne, group: Group, message: MessageChain = DetectPrefix("/ai帮助")
):
    await app.send_group_message(
        group,
        MessageChain(
            Plain(
                "欢迎使用\n第一次使用请先选择模型'/选择模型 1'或'/选择模型 2'\n模型1: gpt-3.5-turbo\n模型2: gpt-4o\n使用'ai 文本'进行对话"
            )
        ),
    )


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def choose_model(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain = DetectPrefix("/选择模型"),
):
    model_choice = str(message).strip()
    if model_choice not in ["1", "2"]:
        await app.send_group_message(
            group, MessageChain(Plain("请输入'/选择模型 1' 或 '/选择模型 2'"))
        )
        return

    model = "gpt-3.5-turbo" if model_choice == "1" else "gpt-4o"

    # 连接到MongoDB数据库
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        user_collection = client.ai.user
        user_data = {"user_id": member.id, "model": model}
        query_result = user_collection.find_one({"user_id": member.id})
        if query_result:
            await app.send_group_message(group, MessageChain(Plain("您无需初始化")))
            return

        # 插入新的文档
        user_collection.insert_one(user_data)
        await app.send_group_message(
            group, MessageChain(Plain(f"已选择模型 {model_choice}"))
        )


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def ai_duihua(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain = DetectPrefix("/ai"),
):
    user_message = str(message).strip()
    if "帮助" in user_message[:2]:
        return
    
    if not user_message:
        await app.send_group_message(group, MessageChain(Plain("请输入要对话的内容")))
        return

    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        user_collection = client.ai.user
        user_data = user_collection.find_one({"user_id": member.id})

        if not user_data:
            await app.send_group_message(
                group,
                MessageChain(Plain("请先选择模型 '/选择模型 1' 或 '/选择模型 2'")),
            )
            return

        model = user_data["model"]

        expired, latest_timestamp = await is_session_expired(member.id)

        if expired:
            await app.send_group_message(
                group,
                MessageChain(
                    Plain(f"您的会话已过期，上次会话时间为：{latest_timestamp}。")
                ),
            )
            return

        response = await call_chatgpt_api(user_message, model)
        await app.send_group_message(group, MessageChain(Plain(str(response))))
        # 保存当前会话记录
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_id": member.id,
            "prompt": user_message,
            "response": response,
        }
        await save_conversation(member.id, conversation)

        await app.send_group_message(group, MessageChain(Plain(response)))
