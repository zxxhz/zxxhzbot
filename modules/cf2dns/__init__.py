import asyncio
import functools

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from modules.cf2dns.cf2dns import main as cfv4
from modules.cf2dns.cf2dns_v6 import main as cfv6

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def cf2dns(
    app: Ariadne,
    group: Group,
    member: Member,
    message: MessageChain = MatchContent("cf优选ip"),
):
    if member.id != 1582891850:
        return
    loop = asyncio.get_event_loop()
    cfv4_partial = functools.partial(cfv4, 1)
    cfv6_partial = functools.partial(cfv6, 1)
    await loop.run_in_executor(None, cfv4_partial)
    await loop.run_in_executor(None, cfv6_partial)
    await app.send_message(group, MessageChain(Plain("已成功更新优选ip")))
