from datetime import datetime, timezone, timedelta
import asyncio
import feedparser
import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graiax.playwright import PlaywrightBrowser

# 获取 Channel 对象
channel = Channel.current()

# 文件路径用于保存上一次的条目链接
file_path = "modules/rss/previous_entries.json"
previous_entries = ""


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[DetectPrefix("开启博客rss订阅")]
    )
)
async def send_rss(app: Ariadne, group: Group, member: Member):
    """
    发送群消息响应的异步函数，用于回复接收到的请求。

    Args:
        app (Ariadne): Ariadne 实例
        group (Group): Group 实例
    """
    global previous_entries
    if member.id != 1582891850:
        return None
    # 发送简单的回复消息
    # 从文件加载上一次的条目链接
    previous_entries = await load_previous_entries()
    await main(app, group)
    # await app.send_message(group, MessageChain(Plain("已开启博客rss订阅")))


async def parse_pub_date(pub_date_str):
    """
    解析 RSS 条目的发布日期字符串为 datetime 对象。

    Args:
        pub_date_str (str): 发布日期字符串

    Returns:
        datetime: 解析后的发布日期
    """
    # 将字符串解析为 datetime 对象
    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")

    # 将时区设为 UTC
    pub_date = pub_date.replace(tzinfo=timezone.utc)

    # 转换为本地时区
    local_pub_date = pub_date.astimezone(timezone(timedelta(hours=8)))  # 例如，转换为东八区时区

    return local_pub_date


async def fetch_rss(feed_url):
    """
    异步获取指定 RSS feed 的内容。

    Args:
        feed_url (str): RSS feed 的 URL

    Returns:
        str: RSS 内容的文本
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(feed_url) as response:
            return await response.text()


async def read_rss(app: Ariadne, group):
    """
    异步读取指定 RSS feed 的条目信息。

    Args:
        feed_url (str): RSS feed 的 URL
        num_entries (int, optional): 需要读取的条目数量，默认为 5
    """
    global previous_entries
    feed_url = "https://www.0cy.me/rss.xml"  # 替换成你的 RSS feed 的 URL
    num_entries = 5

    # 获取 RSS 内容
    rss_content = await fetch_rss(feed_url)
    feed = feedparser.parse(rss_content)

    # group = 614985651

    print(f"网站名称: {feed.feed.title}")
    # print(f"Feed Description: {feed.feed.description}")

    # 获取当前条目链接的集合
    current_entries = {entry.link for entry in feed.entries[:num_entries]}

    # 检查是否有新的条目
    new_entries = list(current_entries - previous_entries)

    if new_entries:
        print("New Entries:")
        for entry_link in new_entries:
            entry = next(
                (entry for entry in feed.entries if entry.link == entry_link), None
            )
            if entry:
                await app.send_message(
                    group, MessageChain(Plain(f"网站名称: {feed.feed.title}"))
                )
                await app.send_message(
                    group, MessageChain(Plain(f"文章标题: {entry.title}"))
                )
                await app.send_message(
                    group, MessageChain(Plain(f"文章链接: {entry.link}"))
                )
                # print(f"Entry Description: {entry.description}")
                await app.send_message(
                    group,
                    MessageChain(
                        Plain(f"发布时间: {await parse_pub_date(entry.published)}")
                    ),
                )  # 解析并显示发布时间
                # print(
                #     f"Current Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                # )  # 当前本地时间

    # 更新上一次的条目链接集合
    previous_entries = current_entries

    # 保存当前的条目链接到文件
    with open(file_path, "w") as file:
        file.write("\n".join(current_entries))


async def load_previous_entries():
    """
    异步从文件加载上一次的条目链接。

    Returns:
        Set: 包含上一次的条目链接的集合
    """
    try:
        with open(file_path, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()


async def main(app, group):
    """
    异步主程序，每隔半小时运行一次 read_rss 函数。
    """
    while True:
        await read_rss(app, group)
        await asyncio.sleep(1800)  # 等待30分钟


if __name__ == "__main__":
    asyncio.run(main())
