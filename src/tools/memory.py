"""Memory tools for Deep Research system."""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from src.tools.base import BaseTool
from src.utils.logger import logger
from src.utils.config import config


class MemoryStoreTool(BaseTool):
    """Tool for storing and retrieving information from memory."""
    
    def __init__(self):
        super().__init__(
            name="memory_store",
            description="Store and retrieve information from persistent memory."
        )
        self.db_path = config.database_path
        self._init_database()
        
    def _init_database(self):
        """Initialize the database."""
        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id TEXT UNIQUE NOT NULL,
                query TEXT NOT NULL,
                plan TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized database at {self.db_path}")
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute memory operation.
        
        Args:
            action: Action to perform (save, retrieve, list, delete)
            **kwargs: Additional parameters
            
        Returns:
            Operation result
        """
        if action == "save":
            return await self._save(**kwargs)
        elif action == "retrieve":
            return await self._retrieve(**kwargs)
        elif action == "list":
            return await self._list(**kwargs)
        elif action == "delete":
            return await self._delete(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def _save(self, key: str, value: Any, type: str = "general") -> Dict[str, Any]:
        """Save to memory.
        
        Args:
            key: Memory key
            value: Value to store
            type: Type of memory (general, plan, result, etc.)
            
        Returns:
            Save result
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Serialize value to JSON
            value_json = json.dumps(value)
            
            # Insert or update
            cursor.execute("""
                INSERT INTO memory (key, value, type)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    type = excluded.type,
                    updated_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
            """, (key, value_json, type))
            
            conn.commit()
            
            logger.debug(f"Saved to memory: {key}")
            return {
                "key": key,
                "saved": True
            }
            
        except Exception as e:
            logger.error(f"Failed to save to memory: {e}")
            return {
                "key": key,
                "saved": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _retrieve(self, key: str) -> Dict[str, Any]:
        """Retrieve from memory.
        
        Args:
            key: Memory key
            
        Returns:
            Retrieved value
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Get value
            cursor.execute("""
                SELECT value, type, created_at, updated_at, access_count
                FROM memory
                WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            
            if row:
                # Update access count
                cursor.execute("""
                    UPDATE memory
                    SET access_count = access_count + 1
                    WHERE key = ?
                """, (key,))
                conn.commit()
                
                value = json.loads(row[0])
                return {
                    "key": key,
                    "value": value,
                    "type": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "access_count": row[4] + 1,
                    "found": True
                }
            else:
                return {
                    "key": key,
                    "found": False
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve from memory: {e}")
            return {
                "key": key,
                "found": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _list(self, type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """List memory entries.
        
        Args:
            type: Filter by type
            limit: Maximum entries to return
            
        Returns:
            List of memory entries
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            if type:
                cursor.execute("""
                    SELECT key, type, updated_at, access_count
                    FROM memory
                    WHERE type = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (type, limit))
            else:
                cursor.execute("""
                    SELECT key, type, updated_at, access_count
                    FROM memory
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entries.append({
                    "key": row[0],
                    "type": row[1],
                    "updated_at": row[2],
                    "access_count": row[3]
                })
            
            return {
                "entries": entries,
                "count": len(entries)
            }
            
        except Exception as e:
            logger.error(f"Failed to list memory: {e}")
            return {
                "entries": [],
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _delete(self, key: str) -> Dict[str, Any]:
        """Delete from memory.
        
        Args:
            key: Memory key
            
        Returns:
            Delete result
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            
            return {
                "key": key,
                "deleted": deleted
            }
            
        except Exception as e:
            logger.error(f"Failed to delete from memory: {e}")
            return {
                "key": key,
                "deleted": False,
                "error": str(e)
            }
        finally:
            conn.close()


class ResearchPlanMemory(BaseTool):
    """Tool for managing research plans."""
    
    def __init__(self):
        super().__init__(
            name="research_plan_memory",
            description="Store and manage research plans."
        )
        self.db_path = config.database_path
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute research plan operation.
        
        Args:
            action: Action to perform (save, get, update, list)
            **kwargs: Additional parameters
            
        Returns:
            Operation result
        """
        if action == "save":
            return await self._save_plan(**kwargs)
        elif action == "get":
            return await self._get_plan(**kwargs)
        elif action == "update":
            return await self._update_plan(**kwargs)
        elif action == "list":
            return await self._list_plans(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def _save_plan(
        self, 
        query_id: str, 
        query: str, 
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save research plan."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            plan_json = json.dumps(plan)
            
            cursor.execute("""
                INSERT INTO research_plans (query_id, query, plan)
                VALUES (?, ?, ?)
            """, (query_id, query, plan_json))
            
            conn.commit()
            
            return {
                "query_id": query_id,
                "saved": True
            }
            
        except Exception as e:
            logger.error(f"Failed to save research plan: {e}")
            return {
                "query_id": query_id,
                "saved": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _get_plan(self, query_id: str) -> Dict[str, Any]:
        """Get research plan."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT query, plan, status, created_at, updated_at
                FROM research_plans
                WHERE query_id = ?
            """, (query_id,))
            
            row = cursor.fetchone()
            
            if row:
                plan = json.loads(row[1])
                return {
                    "query_id": query_id,
                    "query": row[0],
                    "plan": plan,
                    "status": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "found": True
                }
            else:
                return {
                    "query_id": query_id,
                    "found": False
                }
                
        except Exception as e:
            logger.error(f"Failed to get research plan: {e}")
            return {
                "query_id": query_id,
                "found": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _update_plan(
        self, 
        query_id: str, 
        status: Optional[str] = None,
        progress: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Update research plan."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute("""
                    UPDATE research_plans
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE query_id = ?
                """, (status, query_id))
            
            if progress:
                # Get current plan
                cursor.execute("""
                    SELECT plan FROM research_plans WHERE query_id = ?
                """, (query_id,))
                
                row = cursor.fetchone()
                if row:
                    plan = json.loads(row[0])
                    plan["progress"] = progress
                    
                    cursor.execute("""
                        UPDATE research_plans
                        SET plan = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE query_id = ?
                    """, (json.dumps(plan), query_id))
            
            conn.commit()
            
            return {
                "query_id": query_id,
                "updated": cursor.rowcount > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to update research plan: {e}")
            return {
                "query_id": query_id,
                "updated": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def _list_plans(
        self, 
        status: Optional[str] = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """List research plans."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute("""
                    SELECT query_id, query, status, created_at, updated_at
                    FROM research_plans
                    WHERE status = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT query_id, query, status, created_at, updated_at
                    FROM research_plans
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            plans = []
            for row in rows:
                plans.append({
                    "query_id": row[0],
                    "query": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            
            return {
                "plans": plans,
                "count": len(plans)
            }
            
        except Exception as e:
            logger.error(f"Failed to list research plans: {e}")
            return {
                "plans": [],
                "error": str(e)
            }
        finally:
            conn.close()