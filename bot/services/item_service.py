import json
from typing import List, Dict, Optional
from database.db import get_pool


class ItemService:
    """Сервис для работы с предметами пользователя"""

    @staticmethod
    async def get_user_items(user_id: int) -> List[Dict]:
        """Получить все предметы пользователя"""
        pool = await get_pool()
        row = await pool.fetchrow(
            "SELECT subgroups FROM users WHERE telegram_id = $1",
            user_id
        )
        if not row or not row['subgroups']:
            return []
        subgroups = json.loads(row['subgroups']) if isinstance(row['subgroups'], str) else row['subgroups']
        return subgroups

    @staticmethod
    async def get_user_main_group(user_id: int) -> Optional[str]:
        """Получить основную группу пользователя"""
        pool = await get_pool()
        row = await pool.fetchrow(
            "SELECT primary_group FROM users WHERE telegram_id = $1",
            user_id
        )
        return row['primary_group'] if row else None

    @staticmethod
    async def get_all_subjects() -> List[str]:
        """Получить все предметы из расписания"""
        pool = await get_pool()
        rows = await pool.fetch("SELECT DISTINCT subject FROM schedule ORDER BY subject")
        return [row['subject'] for row in rows]

    @staticmethod
    async def get_available_subgroups(subject: str, group: str) -> List[str]:
        """Получить доступные подгруппы для предмета в группе"""
        pool = await get_pool()
        rows = await pool.fetch(
            """
            SELECT DISTINCT subgroup_name FROM schedule
            WHERE subject = $1 AND group_name = $2 
            AND subgroup_name IS NOT NULL AND subgroup_name != ''
            ORDER BY subgroup_name
            """,
            subject, group
        )
        return [row['subgroup_name'] for row in rows]

    @staticmethod
    async def subject_exists(subject: str) -> bool:
        """Проверить существование предмета в расписании"""
        pool = await get_pool()
        exists = await pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM schedule WHERE subject = $1 LIMIT 1)",
            subject
        )
        return exists

    @staticmethod
    async def group_exists(group: str) -> bool:
        """Проверить существование группы в расписании"""
        pool = await get_pool()
        exists = await pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM schedule WHERE group_name = $1 LIMIT 1)",
            group
        )
        return exists

    @staticmethod
    async def add_item(user_id: int, subject: str, subgroup: str) -> bool:
        """Добавить предмет пользователю"""
        pool = await get_pool()
        
        row = await pool.fetchrow(
            "SELECT subgroups FROM users WHERE telegram_id = $1",
            user_id
        )
        
        subgroups = []
        if row and row['subgroups']:
            subgroups = json.loads(row['subgroups']) if isinstance(row['subgroups'], str) else row['subgroups']
        
        for item in subgroups:
            if item.get('name', '').lower() == subject.lower():
                return False
        
        subgroups.append({'name': subject, 'subgroup': subgroup})
        
        await pool.execute(
            "UPDATE users SET subgroups = $1::jsonb WHERE telegram_id = $2",
            json.dumps(subgroups, ensure_ascii=False),
            user_id
        )
        return True

    @staticmethod
    async def update_item(user_id: int, subject: str, new_subgroup: str) -> bool:
        """Обновить подгруппу предмета"""
        pool = await get_pool()
        
        row = await pool.fetchrow(
            "SELECT subgroups FROM users WHERE telegram_id = $1",
            user_id
        )
        
        if not row or not row['subgroups']:
            return False
        
        subgroups = json.loads(row['subgroups']) if isinstance(row['subgroups'], str) else row['subgroups']
        
        for item in subgroups:
            if item.get('name', '').lower() == subject.lower():
                item['subgroup'] = new_subgroup
                break
        else:
            return False
        
        await pool.execute(
            "UPDATE users SET subgroups = $1::jsonb WHERE telegram_id = $2",
            json.dumps(subgroups, ensure_ascii=False),
            user_id
        )
        return True

    @staticmethod
    async def delete_item(user_id: int, subject: str) -> bool:
        """Удалить предмет у пользователя"""
        pool = await get_pool()
        
        row = await pool.fetchrow(
            "SELECT subgroups FROM users WHERE telegram_id = $1",
            user_id
        )
        
        if not row or not row['subgroups']:
            return False
        
        subgroups = json.loads(row['subgroups']) if isinstance(row['subgroups'], str) else row['subgroups']
        new_subgroups = [item for item in subgroups if item.get('name', '').lower() != subject.lower()]
        
        if len(new_subgroups) == len(subgroups):
            return False
        
        await pool.execute(
            "UPDATE users SET subgroups = $1::jsonb WHERE telegram_id = $2",
            json.dumps(new_subgroups, ensure_ascii=False),
            user_id
        )
        return True

    @staticmethod
    async def change_group(user_id: int, new_group: str) -> List[Dict]:
        """Сменить основную группу и пересоздать предметы"""
        pool = await get_pool()
        
        subjects = await pool.fetch(
            "SELECT DISTINCT subject FROM schedule WHERE group_name = $1 ORDER BY subject",
            new_group
        )
        
        subgroups = [
            {'name': subject['subject'], 'subgroup': f"Основная группа ({new_group})"}
            for subject in subjects
        ]
        
        await pool.execute(
            "UPDATE users SET primary_group = $1, subgroups = $2::jsonb WHERE telegram_id = $3",
            new_group,
            json.dumps(subgroups, ensure_ascii=False),
            user_id
        )
        return subgroups

    @staticmethod
    async def get_all_groups() -> List[str]:
        """Получить все группы из расписания"""
        pool = await get_pool()
        rows = await pool.fetch("SELECT DISTINCT group_name FROM schedule ORDER BY group_name")
        return [row['group_name'] for row in rows]