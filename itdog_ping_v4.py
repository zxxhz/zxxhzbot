import asyncio

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
async def ping_v4(
    app: Ariadne, group: Group, message: MessageChain = DetectPrefix("ping")
):
    """itdogping并发送搜索结果截图

    Args:
        app (Ariadne): 初始化
        group (Group): 发送的群
        message (MessageChain, optional): 接受到的消息默认删除("ping").
    """
    launart = app.launch_manager
    keyword = message.display.strip()
    browser = launart.get_interface(PlaywrightBrowser)
    # 此处的 browser 之用法与 playwright.async_api.Browser 无异，但要注意的是下方代码的返回值为 False。
    # `isinstance(browser, playwright.async_api.Browser)`
    await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
    async with browser.page(  # 此 API 启用了自动上下文管理
        viewport={"width": 800, "height": 10},
        device_scale_factor=1.5,
    ) as page:
        await page.goto(f"https://www.itdog.cn/ping/{keyword}")
        await page.get_by_role("button", name=" 单次测试").click()
        await page.get_by_text("关闭所有广告").first.click()
        await asyncio.sleep(10)
        img = await page.locator("canvas").screenshot(
            type="jpeg", quality=80, scale="device"
        )

    await app.send_message(group, MessageChain(Image(data_bytes=img)))
