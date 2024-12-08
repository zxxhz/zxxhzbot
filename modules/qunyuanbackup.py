import csv
import time
from pathlib import Path
from typing import List, Dict, Any

import aiofiles
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

channel = Channel.current()

# 常量配置
BACKUP_DIR = Path("./qunyuanbackup")
ADMIN_QQ = 1582891850

# 确保备份目录存在
BACKUP_DIR.mkdir(exist_ok=True)

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], 
        decorators=[DetectPrefix("备份群成员列表")]
    )
)
async def backup(app: Ariadne, group: Group, member: Member) -> None:
    """备份群成员列表到CSV文件
    
    Args:
        app: Ariadne 实例
        group: 当前群组
        member: 发送命令的成员
    """
    if member.id != ADMIN_QQ:
        await app.send_group_message(group, MessageChain([Plain("权限不足")]))
        return

    try:
        await app.send_group_message(
            group, MessageChain([Plain("正在获取群成员信息，请稍候...")])
        )
        
        member_list = await app.get_member_list(group)
        filename = f"{time.strftime('%Y%m%d-%H%M%S')}_{group.id}.csv"
        file_path = BACKUP_DIR / filename
        
        await save_members_to_csv(member_list, file_path)
        
        # 读取并上传文件
        try:
            with open(file_path, "rb") as f:
                csv_bytes = f.read()
            await app.upload_file(csv_bytes, "group", group, name=filename)
            await app.send_group_message(
                group, MessageChain([Plain("群成员数据已保存并上传到群文件")])
            )
        except Exception as e:
            await app.send_group_message(
                group, MessageChain([Plain(f"文件上传失败: {str(e)}")])
            )
            
    except Exception as e:
        await app.send_group_message(
            group, MessageChain([Plain(f"备份过程出现错误: {str(e)}")])
        )

async def save_members_to_csv(members: List[Member], file_path: Path) -> None:
    """将群成员数据保存为CSV文件
    
    Args:
        members: 群成员列表
        file_path: CSV文件保存路径
    """
    parsed_data = [
        {
            "id": member.id,
            "name": member.name,
            "permission": member.permission,
            "join_timestamp": member.join_timestamp,
            "last_speak_timestamp": member.last_speak_timestamp,
            "mute_time": member.mute_time,
            "group_id": member.group.id,
            "group_name": member.group.name,
            "account_perm": member.group.account_perm,
        }
        for member in members
    ]

    async with aiofiles.open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=parsed_data[0].keys())
        await writer.writeheader()
        for row in parsed_data:
            await writer.writerow(row)
