import csv
import time
import aiofiles
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[DetectPrefix("获取群成员")]
    )
)
async def diaotu_upload(app: Ariadne, group: Group, member: Member):
    """_summary_

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        member (Member): 发送的群成员

    Returns:
        _type_: 忽略不计
    """
    if member.id != 1582891850:
        await app.send_group_message(group, MessageChain([Plain("权限不足")]))
        return None
    await app.send_group_message(
        group, MessageChain([Plain("正在获取群成员信息，请稍候...")])
    )
    member_list = await app.get_member_list(group)
    await app.send_group_message(
        group, MessageChain([Plain(f"群成员信息已获取，共有{len(member_list)}人")])
    )
    await save_members_to_csv(member_list,f"{time.strftime('%Y%m%d',time.localtime())}_{group.id}")
    await app.send_group_message(group, MessageChain([Plain("群成员信息已保存")]))
    # await app.send_group_message(
    #     group, MessageChain([Plain("默认自动上传数据到群文件")])
    # )


async def save_members_to_csv(data, filename):
    """_summary_

    Args:
        data (List): 需要保存的群数据
        filename (Str): 保存的文件名
    """
    # 解析数据
    parsed_data = []
    for member in data:
        member_data = {}
        member = str(member)
        member_data["id"] = int(member.split("(")[1].split(",")[0].split("=")[1])
        member_data["name"] = member.split("name='")[1].split("',")[0]
        member_data["permission"] = member.split("permission=<")[1].split(">")[0]
        member_data["join_timestamp"] = int(
            member.split("join_timestamp=")[1].split(",")[0]
        )
        member_data["last_speak_timestamp"] = int(
            member.split("last_speak_timestamp=")[1].split(",")[0]
        )
        member_data["mute_time"] = member.split("mute_time=")[1].split(",")[0]
        member_data["group_id"] = int(member.split("group=Group(id=")[1].split(",")[0])
        member_data["group_name"] = member.split("group=Group(name='")[1].split("',")[0]
        member_data["account_perm"] = member.split("account_perm=<")[1].split(">")[0]
        member_data["muteTimeRemaining"] = int(
            member.split("muteTimeRemaining=")[1].split(")")[0]
        )
        parsed_data.append(member_data)

    # 异步写入CSV
    filename = f"./qunyuanbackup/{filename}.csv"
    async with aiofiles.open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=parsed_data[0].keys())
        await writer.writeheader()
        for row in parsed_data:
            await writer.writerow(row)
