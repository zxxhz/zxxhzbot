import os
import time

import requests
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pymongo import MongoClient

channel = Channel.current()
UPLOAD = "草图上传"
KEY = "来个草图"
DIAOTU = "diaotu"
SUPERADMIN = ["1582891850"]


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix(UPLOAD)])
)
async def diaotu_upload(
    app: Ariadne, group: Group, message: MessageChain, member: Member
):
    """上传草图

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        message (MessageChain): 接受到的消息
        member (Member): 发送者

    Returns:
        _type_: _description_
    """
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        admin = client.caotu.admin
        admin_search = {"qq": str(member.id)}
        if admin.find_one(admin_search) is None:
            await app.send_message(group, MessageChain(Plain("你不是管理员不能添加表情￣へ￣")))
            return

    await app.send_message(group, MessageChain(Plain("请在1分钟内发送要收藏的表情,超时自动失效")))

    async def waiter(
        waiter_message: MessageChain, group_two: Group, member_two: Member
    ):
        if group_two == group and member_two == member:
            image = waiter_message
            if image.display != "[图片]":
                return "bad"
            image_url = image.get_first(Image).url
            image_id = image.get_first(Image).id
            # 连接数据库存入图片名字,并判断是否有重复的图片id
            with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
                photo = client.caotu.photos
                photo_add = {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "qun": group.id,
                    "qq": member.id,
                    "photo_name": image_id,
                }

                query = {"photo_name": image_id}
                query_result = photo.find_one(query)
                if query_result:
                    return "same"
                # 如果不存在，则插入数据并保存图片
                photo.insert_one(photo_add)
                r = requests.get(image_url, timeout=10)
                with open(f"./{DIAOTU}/{image_id}", mode="wb") as f:
                    f.write(r.content)
                # TODO: 以后添加给图片编号
                return image

    result = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=60)

    if result is None:
        await app.send_message(group, MessageChain(Plain("添加超时")))
        return

    if result == "bad":
        await app.send_message(group, MessageChain(Plain("添加失败")))
        return

    if result == "same":
        await app.send_message(group, MessageChain(Plain("数据库中已存在相同的图片!")))
        return

    await app.send_message(group, MessageChain(Plain("添加成功")))


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix(KEY)])
)
async def diaotu_send(app: Ariadne, group: Group):
    """发送草图

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
    """
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        photo = client.caotu.photos
        photo_name = list(photo.find().limit(1))[0]["photo_name"]

    with open(f"./{DIAOTU}/{photo_name}", "rb") as f:
        image_bytes = f.read()
    await app.send_message(group, MessageChain(Image(data_bytes=image_bytes)))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def admin_add(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain = DetectPrefix("添加管理员"),
):
    """添加管理员

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        member (Member): 发送者
        message (MessageChain, optional): 接收消息. 默认去除前缀("添加管理员").
    """
    # 判断成员 ID 是否在超级管理员列表中，不在则继续执行
    if str(member.id) not in SUPERADMIN:
        return
    # 获取成员发送的消息
    message = message.display.strip()
    # 如果消息中包含"@"，则获取"@"后面的内容作为管理员 QQ
    if "@" in message:
        message = message.split("@")[1]
    # 连接 MongoDB 数据库
    with MongoClient("mongodb://zxxhz:zxxhz@localhost:27017/") as client:
        # 获取 admin 集合
        admin = client.caotu.admin
        # 创建一个新的管理员文档，包含"qq"字段和相应的值
        admin_add = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "qq": message,
        }
        # 使用 find_one 方法查询集合中是否已存在该管理员，如果不存在则插入新的文档
        if admin.find_one(admin_add) is None:
            admin.insert_one(admin_add)
            # 添加成功后发送消息通知
            await app.send_message(group, MessageChain(Plain("添加管理员成功")))
            return
    # 如果已存在，则发送消息告知该管理员已存在
    await app.send_message(group, MessageChain(Plain("此管理员已存在数据库中")))


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix("草图帮助")])
)
async def caotu_help(app: Ariadne, group: Group):
    """草图帮助

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
    """
    await app.send_group_message(
        group,
        MessageChain(
            Plain(
                f"草图帮助\n获取草图命令: {KEY}\n草图上传命令(认证管理员): {UPLOAD}\n添加管理员命令(超级管理员): 添加管理员[@QQ/QQ]"
            )
        ),
    )
