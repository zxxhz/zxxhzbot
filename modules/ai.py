from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pymongo import MongoClient

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def ai_help(
    app: Ariadne, group: Group, message: MessageChain = DetectPrefix("ai帮助")
):
    await app.send_group_message(group, MessageChain(Plain("欢迎使用\n第一次使用请先选择模型'选择模型 1'或'选择模型 2'\n模型1: gpt-3.5-turbo模型2: gpt-4o\n使用'ai 文本'进行对话")))

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def choose_model(
    app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix("选择模型")
):
    if not message.strip() in ["1","2"] :
        await app.send_group_message(group, MessageChain(Plain("请输入数字")))
        return None
    model = message.strip()

    # 连接到MongoDB数据库
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        # 获取 user 集合
        user = client.ai.user
        # 创建一个新的文档，包含字段和相应的值
        user = {
            "user": member.id,
            "model": model,
        }
        query_result = user.find_one(user)
        if query_result:
                await app.send_group_message(
                    group, MessageChain(Plain("您无需初始化"))
                )
                return None
        # 插入新的文档
        user.insert_one(user)

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def ai_duihua(
    app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix("ai")
):
    await app.send_group_message(group, MessageChain(Plain("没写好呢,你急什么")))
