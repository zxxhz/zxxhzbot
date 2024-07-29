import re
import time

from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import MemberJoinRequestEvent
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from pymongo import MongoClient

channel = Channel.current()
patterns = [
    r"威联通",
    r"群晖",
    r"极空间",
    r"绿联",
    r"\d{3,5}",
]


@channel.use(ListenerSchema(listening_events=[MemberJoinRequestEvent]))
async def jinqun(
    app: Ariadne,
    event: MemberJoinRequestEvent,
):
    """检测到申请发送消息，并自动判断

    Args:
        app (Ariadne): 初始化
        event (MemberJoinRequestEvent): 申请入群事件
    """
    await app.send_group_message(
        event.source_group, MessageChain(f"申请人：{event.nickname}\n{event.message}")
    )
    if any(re.search(pattern, event.message) for pattern in patterns):
        await event.accept()
        await app.send_group_message(
            event.source_group,
            MessageChain(f"已通过{event.nickname}的入群申请，欢迎进群！"),
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
        # TODO: 生成一段时间内NAS机型的热门程度图表(得鸽好久)

        # 插入新的文档
        user.insert_one(user_add)
