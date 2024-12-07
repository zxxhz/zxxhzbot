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
        listening_events=[GroupMessage], decorators=[DetectPrefix("bot帮助")]
    )
)
async def print_bot_help(app: Ariadne, group: Group, member: Member):
    """显示bot的帮助信息
    
    Args:
        app (Ariadne): Ariadne实例
        group (Group): 群组对象
        member (Member): 发送命令的成员
    """
    # 基础命令列表
    commands = [
        "zxbot命令菜单",
        "草图帮助",
        "网站测速 <域名>",
        "ping <域名>", 
        "百度搜索 <搜索的内容>"
    ]
    
    # 管理员命令列表
    admin_commands = [
        "cf优选ip",
        "备份群成员列表"
    ]
    
    # 拼接基础命令
    text = "\n".join(commands)
    
    # 如果是管理员,添加管理员命令
    if member.id == 1582891850:
        text += "\n" + "\n".join(admin_commands)
        
    await app.send_message(group, MessageChain(Plain(text)))
