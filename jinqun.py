import re
import time

from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import MemberJoinRequestEvent
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from pymongo import MongoClient

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[MemberJoinRequestEvent]))
async def jinqun(
    app: Ariadne,
    event: MemberJoinRequestEvent,
):
    await app.send_group_message(
        event.source_group, MessageChain(f"申请人：{event.nickname}\n{event.message}")
    )
    if re.search(r"\d{3,5}", event.message):
        await event.accept()
        await app.send_group_message(
            event.source_group, MessageChain(f"已通过{event.nickname}的入群申请，欢迎进群！")
        )
    # 连接 MongoDB 数据库
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        # 获取 user 集合
        user = client.jinqun.user
        # 创建一个新的文档，包含字段和相应的值
        user_add = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "qun": event.source_group,
            "qq": event.supplicant,
            "message": event.message,
        }
        # 插入新的文档
        user.insert_one(user_add)
