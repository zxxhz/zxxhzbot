import asyncio
import re

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graiax.playwright import PlaywrightBrowser

channel = Channel.current()
ipv4_pattern = r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
ipv6_pattern = r"^([\da-fA-F]{1,4}:){6}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^::([\da-fA-F]{1,4}:){0,4}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^([\da-fA-F]{1,4}:):([\da-fA-F]{1,4}:){0,3}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^([\da-fA-F]{1,4}:){2}:([\da-fA-F]{1,4}:){0,2}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^([\da-fA-F]{1,4}:){3}:([\da-fA-F]{1,4}:){0,1}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^([\da-fA-F]{1,4}:){4}:((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$|^([\da-fA-F]{1,4}:){7}[\da-fA-F]{1,4}$|^:((:[\da-fA-F]{1,4}){1,6}|:)$|^[\da-fA-F]{1,4}:((:[\da-fA-F]{1,4}){1,5}|:)$|^([\da-fA-F]{1,4}:){2}((:[\da-fA-F]{1,4}){1,4}|:)$|^([\da-fA-F]{1,4}:){3}((:[\da-fA-F]{1,4}){1,3}|:)$|^([\da-fA-F]{1,4}:){4}((:[\da-fA-F]{1,4}){1,2}|:)$|^([\da-fA-F]{1,4}:){5}:([\da-fA-F]{1,4})?$|^([\da-fA-F]{1,4}:){6}:$"
domain_pattern = r"^([a-zA-Z0-9-]+\.){1,}[a-zA-Z]{2,}$"


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def ping(
    app: Ariadne, group: Group, message: MessageChain = DetectPrefix("ping")
):
    """
    itdogping并发送搜索结果截图

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        message (MessageChain, optional): 接受到的消息默认删除("ping")
    """
    keyword = message.display.strip()
    if re.search(domain_pattern, keyword):
        await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
        await visit(app=app, group=group, type="domain", keyword=keyword)

    elif re.search(ipv4_pattern, keyword):
        await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
        await visit(app=app, group=group, type="ipv4", keyword=keyword)

    elif re.search(ipv6_pattern, keyword):
        await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
        await visit(app=app, group=group, type="ipv6", keyword=keyword)

    else:
        return


async def visit(app: Ariadne, group: Group, type: str, keyword: str):
    """
    访问一个网页，使用 Playwright 浏览器并将该网页的截图发送给一个群组。

    Args:
        app(Ariadne): Ariadne 应用程序实例
        group(Group): 要发送截图的群组
        type(str): 截图的类型
        keyword(str): 关键字

    Returns:
        None
    """
    launart = app.launch_manager
    browser = launart.get_interface(PlaywrightBrowser)
    if type == "domain":
        url = "https://www.itdog.cn/ping/"
    if type == "ipv4":
        url = "https://www.itdog.cn/ping/"
    if type == "ipv6":
        url = "https://www.itdog.cn/ping_ipv6/"

    async with browser.page(  # 此 API 启用了自动上下文管理
        viewport={"width": 800, "height": 10},
        device_scale_factor=1.5,
    ) as page:
        await page.goto(url + keyword)
        await page.get_by_role("button", name=" 单次测试").click()
        await asyncio.sleep(10)
        img = await page.locator('//*[@id="china_map"]/div[1]/canvas').screenshot(
            type="jpeg", quality=80, scale="device"
        )

    await app.send_message(group, MessageChain(Image(data_bytes=img)))
