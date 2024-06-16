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
UPLOAD = ["草图上传","上传草图","草图添加","添加草图"]  # 用于标识草图上传操作的字符串
KEY = "来个草图"  # 指定的触发关键词
DIAOTU = "diaotu"  # 可能用于指定某项操作或标识
SUPERADMIN = ["1582891850"]  # 超级管理员ID列表
MONGO_URL = "mongodb://zxxhz:zxxhz@localhost:27017/"  # MongoDB连接URL


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix(UPLOAD)])
)
async def diaotu_upload(app: Ariadne, group: Group, member: Member):
    """
    上传草图到群组表情包收藏。

    Args:
        app (Ariadne): Ariadne 应用实例，用于发送消息和处理群组交互。
        group (Group): 发送消息的群组。
        member (Member): 发送消息的成员。

    Returns:
        None: 表示添加过程超时。
        True: 表示表情包上传并添加成功。
        False: 表示表情包上传失败或已存在。
    """

    # 检查发送者是否为群组管理员
    if not await is_admin(member.id):
        await app.send_group_message(
            group, MessageChain(Plain("你不是管理员不能添加表情￣へ￣"))
        )
        return None

    # 向群组发送提示消息，告知用户需要在限定时间内发送图片
    await app.send_message(
        group, MessageChain(Plain("请在1分钟内发送要收藏的表情,超时自动失效"))
    )

    # 定义一个异步函数，用于等待和处理用户发送的图片消息
    async def waiter(
        waiter_message: MessageChain, group_two: Group, member_two: Member
    ):
        # 验证消息来源和发送者是否符合预期
        if group_two != group or member_two != member:
            return None

        image = waiter_message

        # 检查用户发送的消息是否为图片
        if image.display != "[图片]":
            await app.send_group_message(
                group, MessageChain(Plain(f"请在发送{UPLOAD}后发送要上传的图片"))
            )
            return False

        # 提取图片URL和ID
        image_url = image.get_first(Image).url
        image_id = image.get_first(Image).id

        # 连接数据库，检查图片是否已存在，若不存在则插入新图片数据
        with MongoClient(MONGO_URL) as client:
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
                await app.send_group_message(
                    group, MessageChain(Plain("数据库中已存在相同的图片!"))
                )
                return False

            photo.insert_one(photo_add)

        # 下载图片并保存
        r = requests.get(image_url, timeout=10)
        with open(f"./{DIAOTU}/{image_id}", mode="wb") as f:
            f.write(r.content)

        return True

    # 使用FunctionWaiter等待用户发送的图片消息，超时时间为60秒
    result = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=60)

    # 根据等待结果发送相应的反馈消息
    match result:
        case None:
            await app.send_message(group, MessageChain(Plain("添加超时")))
            return

        case True:
            await app.send_message(group, MessageChain(Plain("添加成功")))
            return

        case False:
            await app.send_message(group, MessageChain(Plain("添加失败")))
            return

        case _:
            return


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix(KEY)])
)
async def diaotu_send(app: Ariadne, group: Group):
    """
    用于从 MongoDB 中获取随机图片并发送到指定的群聊。

    Args:
        app (Ariadne): Ariadne 应用实例，用于发送消息。
        group (Group): 目标群聊对象。
    """
    # 连接到 MongoDB 并获取 photos 集合
    with MongoClient(MONGO_URL) as client:
        photo = client.caotu.photos

        # 从 photos 集合中随机选择一张图片
        photo_name = photo.aggregate([{"$sample": {"size": 1}}]).next()["photo_name"]

    # 读取并准备发送的图片文件
    with open(f"./{DIAOTU}/{photo_name}", "rb") as f:
        image_bytes = f.read()

    # 使用 Ariadne 的接口向指定群聊发送图片消息
    await app.send_group_message(group, MessageChain(Image(data_bytes=image_bytes)))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def admin_add(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain = DetectPrefix("添加管理员"),
):
    """
    用于添加管理员的异步函数。

    Args:
        app (Ariadne): 用于发送消息的Ariadne应用实例。
        group (Group): 消息发送的目标群组。
        member (Member): 发送消息的群成员。
        message (MessageChain, optional): 接收到的消息内容。默认去除前缀("添加管理员")。
    """

    # 检查发送者是否为超级管理员，如果不是则不执行后续操作
    if str(member.id) not in SUPERADMIN:
        return

    # 处理消息，获取要添加的管理员QQ号
    message = message.display.strip()
    if "@" in message:
        message = message.split("@")[1]

    # 连接数据库并操作，添加新的管理员记录
    with MongoClient(MONGO_URL) as client:
        admin = client.caotu.admin

        # 准备新的管理员数据并插入，如果该管理员不存在的话
        admin_add = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "qq": message,
        }
        existing_admin = admin.find_one({"qq": message})
        if existing_admin is None:
            admin.insert_one(admin_add)
            # 发送添加成功的消息
            await app.send_group_message(group, MessageChain(Plain("添加管理员成功")))
            return

    # 如果管理员已存在，则发送消息提醒
    await app.send_group_message(group, MessageChain(Plain("此管理员已存在数据库中")))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[DetectPrefix("草图帮助")]
    )
)
async def caotu_help(app: Ariadne, group: Group):
    """
    草图帮助函数，用于向指定群发送草图相关的帮助信息。

    Args:
        app (Ariadne): Ariadne框架的实例，用于发送消息。
        group (Group): 消息发送的目标群组。

    Returns:
        None: 该函数没有返回值，它异步地向群组发送一条消息。
    """
    # 发送包含草图帮助信息的消息到指定群组
    await app.send_group_message(
        group,
        MessageChain(
            Plain(
                f"草图帮助\n获取草图命令: {KEY}\n草图上传命令(认证管理员): {UPLOAD}\n添加管理员命令(超级管理员): 添加管理员[@QQ/QQ]"
            )
        ),
    )


async def is_admin(qq: int):
    """
    判读是否为管理员

    Args:
        qq (int): qq号

    Returns:
        bool: 如果是管理员返回True，否则返回False
    """
    # 使用MongoDB客户端连接数据库
    with MongoClient(MONGO_URL) as client:
        # 获取admin集合
        admin = client.caotu.admin
        # 查询数据库中是否存在对应qq的管理员记录
        admin_search = admin.find_one({"qq": str(qq)})

        if admin_search is not None:
            return True  # 存在管理员记录，返回True
        return False  # 不存在管理员记录，返回False
