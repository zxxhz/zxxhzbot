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
MONGO_URL = "mongodb://zxxhz:zxxhz@localhost:27017/"


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix(UPLOAD)])
)
async def diaotu_upload(app: Ariadne, group: Group, member: Member):
    """上传草图

    Args:
        app (Ariadne): Ariadne 应用实例
        group (Group): 发送的群
        member (Member): 发送者

    Returns:
        None: 添加超时
        True: 添加成功
        False: 添加失败
    """

    # 检查发送者是否是管理员
    if not await is_admin(member.id):
        await app.send_group_message(group, MessageChain(Plain("你不是管理员不能添加表情￣へ￣")))
        return None

    # 发送上传表情的提示消息
    await app.send_message(group, MessageChain(Plain("请在1分钟内发送要收藏的表情,超时自动失效")))

    # 定义用于等待图片消息的函数
    async def waiter(
        waiter_message: MessageChain, group_two: Group, member_two: Member
    ):
        # 检查消息是否来自正确的群和发送者
        if group_two != group or member_two != member:
            return None

        image = waiter_message

        if image.display != "[图片]":
            await app.send_group_message(
                group, MessageChain(Plain(f"请在发送{UPLOAD}后发送要上传的图片"))
            )
            return False  # 如果消息不是图片，返回 Fasle

        image_url = image.get_first(Image).url
        image_id = image.get_first(Image).id

        # 连接数据库存入图片名字,并判断是否有重复的图片id
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
                # 如果图片已存在，发送消息
                await app.send_group_message(
                    group, MessageChain(Plain("数据库中已存在相同的图片!"))
                )
                return False

            # 如果图片不存在，则插入数据并保存图片
            photo.insert_one(photo_add)

        r = requests.get(image_url, timeout=10)
        with open(f"./{DIAOTU}/{image_id}", mode="wb") as f:
            f.write(r.content)

        return True

    # 等待图片消息，最长等待时间为60秒
    result = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=60)

    match result:
        # 处理超时或失败情况
        case None:
            await app.send_message(group, MessageChain(Plain("添加超时")))
            return

        # 处理成功情况
        case True:
            await app.send_message(group, MessageChain(Plain("添加成功")))
            return
        
        # 处理失败情况
        case False:
            await app.send_message(group, MessageChain(Plain("添加失败")))
            return


        # 其他情况
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
    # 连接到 MongoDB
    with MongoClient(MONGO_URL) as client:
        # 获取 photo 集合
        photo = client.caotu.photos

        # 获取随机图片文档 从文档中获取图片文件名
        photo_name = photo.aggregate([{"$sample": {"size": 1}}]).next()["photo_name"]

    # 打开图片文件并读取其内容
    with open(f"./{DIAOTU}/{photo_name}", "rb") as f:
        image_bytes = f.read()

    # 使用 Ariadne 发送包含图片的消息
    await app.send_group_message(group, MessageChain(Image(data_bytes=image_bytes)))


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
    with MongoClient(MONGO_URL) as client:
        # 获取 admin 集合
        admin = client.caotu.admin
        # 创建一个新的管理员文档，包含"qq"字段和相应的值
        admin_add = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "qq": message,
        }
        # 使用 find_one 方法查询集合中是否已存在该管理员，如果不存在则插入新的文档
        existing_admin = admin.find_one({"qq": message})
        if existing_admin is None:
            admin.insert_one(admin_add)
            # 添加成功后发送消息通知
            await app.send_group_message(group, MessageChain(Plain("添加管理员成功")))
            return
    # 如果已存在，则发送消息告知该管理员已存在
    await app.send_group_message(group, MessageChain(Plain("此管理员已存在数据库中")))


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


async def is_admin(qq: int):
    """判读是否为管理员

    Args:
        qq (int): qq号

    Returns:
        True: 是管理员
        False: 不是管理员
    """
    with MongoClient(MONGO_URL) as client:
        admin = client.caotu.admin
        admin_search = admin.find_one({"qq": str(qq)})
        if admin_search is not None:
            return True  # 是管理员
        return False  # 不是管理员
