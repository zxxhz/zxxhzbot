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
    text = "zxbot命令菜单\n草图帮助\n网站测速 <域名>\nping <域名>\n百度搜索 <搜索的内容>"
    if member.id == 1582891850:
        text += "\ncf优选ip\n备份群成员列表"
    await app.send_message(group, MessageChain(Plain(text)))