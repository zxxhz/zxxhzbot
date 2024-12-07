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


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def http_speedtest(
    app: Ariadne, group: Group, message: MessageChain = DetectPrefix("网站测速")
):
    """
    itdogping并发送搜索结果截图

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        message (MessageChain, optional): 接受到的消息默认删除("网站测速")
    """
    keyword = message.display.strip()
    await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
    await visit(app=app, group=group, keyword=keyword)


async def visit(app: Ariadne, group: Group, keyword: str):
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
    url = "https://www.itdog.cn/http/"

    async with browser.page(  # 此 API 启用了自动上下文管理
        viewport={"width": 800, "height": 10},
        device_scale_factor=1.5,
    ) as page:
        with open("./modules/stealth.min.js", "r", encoding="utf-8") as f:
            js = f.read()
        await page.add_init_script(js)
        await page.goto(url)
        await page.get_by_placeholder("例：example.com 、https://").fill(keyword)
        await page.get_by_role("button", name=" 快速测试").click()
        await asyncio.sleep(10)
        img = await page.locator('//*[@id="china_map"]').screenshot(
            type="jpeg", quality=80, scale="device"
        )

    await app.send_message(group, MessageChain(Image(data_bytes=img)))
