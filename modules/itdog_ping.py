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


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix("ping")]))
async def ping(app: Ariadne, group: Group, message: MessageChain):
    """
    使用itdog.cn的ping工具测试指定域名或IP的连通性,并返回全国各地的测速结果图表

    Args:
        app (Ariadne): Ariadne应用实例
        group (Group): 消息发送的群组
        message (MessageChain): 接收到的消息,没去除前缀"ping"
    """
    # 去除前缀"ping"并清理空格
    keyword = message.display.strip()[4:].strip()
    
    # 如果关键词为空则返回
    if not keyword:
        return
        
    # 使用字典映射不同类型的匹配模式
    patterns = {
        "domain": domain_pattern,
        "ipv4": ipv4_pattern, 
        "ipv6": ipv6_pattern
    }
    
    # 遍历匹配模式判断类型
    for type_name, pattern in patterns.items():
        if re.search(pattern, keyword):
            await app.send_message(group, MessageChain(Plain("已收到请求，请稍等")))
            await visit(app=app, group=group, type=type_name, keyword=keyword)
            return
            
    # 如果都不匹配则提示格式错误
    await app.send_message(group, MessageChain(Plain("请输入正确的域名或IP地址格式")))


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
    # 使用常量定义URL
    BASE_URL = "https://www.itdog.cn/ping/"
    IPV6_URL = "https://www.itdog.cn/ping_ipv6/"
    
    # 缓存stealth.js内容
    STEALTH_JS = None
    if not STEALTH_JS:
        with open('./modules/stealth.min.js','r',encoding="utf-8") as f:
            STEALTH_JS = f.read()
            
    launart = app.launch_manager
    browser = launart.get_interface(PlaywrightBrowser)
    url = IPV6_URL if type == "ipv6" else BASE_URL

    async with browser.page(
        viewport={"width": 800, "height": 10},
        device_scale_factor=1.5,
    ) as page:
        # 添加反反爬虫脚本
        await page.add_init_script(STEALTH_JS)
        
        try:
            # 设置超时时间
            await page.goto(url + keyword, timeout=10000)
            await page.get_by_role("button", name=" 单次测试").click()
            await asyncio.sleep(10)
            
            # 等待地图元素出现并截图
            map_element = page.locator('//*[@id="china_map"]')
            img = await map_element.screenshot(
                type="jpeg",
                quality=80,
                scale="device"
            )
            
            await app.send_message(group, MessageChain(Image(data_bytes=img)))
            
        except Exception as e:
            await app.send_message(group, MessageChain(f"访问出错: {str(e)}"))
