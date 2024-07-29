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
    ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix("获取群成员")])
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
    await app.send_group_message(group, MessageChain([Plain("正在获取群成员信息，请稍候...")]))
    member_list = await app.get_member_list(group)
    await app.send_group_message(group, MessageChain([Plain(f"群成员信息已获取，共有{len(member_list)}人")]))
    await app.send_group_message(group, MessageChain([Plain(f"{member_list}")]))
