from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import FuzzyMatch
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            FuzzyMatch("来个草图", min_rate=0.6)
        ],  # min_rate 限定了最低匹配阈值
    )
)
async def on_fuzzy_match(app: Ariadne, group: Group, chain: MessageChain):
    await app.send_message(group, MessageChain(Plain("rate")))
    return
    # 我们就假定 rate >= 0.8 是对的
