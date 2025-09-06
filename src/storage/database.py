"""Database storage for research memory and plans."""

import json
import aiosqlite
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from src.utils.logger import logger


class ResearchDatabase:
    """SQLite database for persisting research data."""
    
    def __init__(self, db_path: str = "data/research.db"):
        """Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Research plans table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_plans (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    query_type TEXT,
                    complexity TEXT,
                    plan_data TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Subagent results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subagent_results (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT,
                    agent_id TEXT,
                    task TEXT,
                    results TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES research_plans(id)
                )
            """)
            
            # Memory store table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    category TEXT DEFAULT 'general',
                    access_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Research reports table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_reports (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT,
                    query TEXT,
                    report TEXT,
                    cited_report TEXT,
                    sources TEXT,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES research_plans(id)
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    # Research Plans
    
    async def save_research_plan(self, plan_id: str, query: str, plan: Dict[str, Any]) -> bool:
        """Save a research plan.
        
        Args:
            plan_id: Unique ID for the plan
            query: Original query
            plan: Plan dictionary
            
        Returns:
            Success status
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO research_plans (id, query, query_type, complexity, plan_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    plan_id,
                    query,
                    plan.get("query_type", ""),
                    plan.get("complexity", ""),
                    json.dumps(plan)
                ))
                await db.commit()
                logger.info(f"Saved research plan: {plan_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save research plan: {e}")
            return False
    
    async def get_research_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a research plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan data or None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT plan_data FROM research_plans WHERE id = ?
                """, (plan_id,))
                row = await cursor.fetchone()
                
                if row:
                    return json.loads(row[0])
                return None
        except Exception as e:
            logger.error(f"Failed to get research plan: {e}")
            return None
    
    async def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status.
        
        Args:
            plan_id: Plan ID
            status: New status
            
        Returns:
            Success status
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE research_plans 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, plan_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update plan status: {e}")
            return False
    
    # Subagent Results
    
    async def save_subagent_result(self, plan_id: str, agent_id: str, 
                                   task: str, results: Dict[str, Any]) -> bool:
        """Save subagent results.
        
        Args:
            plan_id: Associated plan ID
            agent_id: Subagent ID
            task: Task description
            results: Results dictionary
            
        Returns:
            Success status
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                result_id = f"{plan_id}_{agent_id}"
                await db.execute("""
                    INSERT INTO subagent_results (id, plan_id, agent_id, task, results, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result_id,
                    plan_id,
                    agent_id,
                    task,
                    json.dumps(results),
                    results.get("status", "completed")
                ))
                await db.commit()
                logger.info(f"Saved subagent result: {agent_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save subagent result: {e}")
            return False
    
    async def get_plan_results(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all results for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List of results
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT agent_id, task, results, status, created_at
                    FROM subagent_results 
                    WHERE plan_id = ?
                    ORDER BY created_at
                """, (plan_id,))
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "agent_id": row[0],
                        "task": row[1],
                        "results": json.loads(row[2]),
                        "status": row[3],
                        "created_at": row[4]
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to get plan results: {e}")
            return []
    
    # Memory Store
    
    async def save_memory(self, key: str, value: Any, category: str = "general") -> bool:
        """Save to memory store.
        
        Args:
            key: Memory key
            value: Value to store
            category: Memory category
            
        Returns:
            Success status
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Try to update first
                cursor = await db.execute("""
                    UPDATE memory_store 
                    SET value = ?, access_count = access_count + 1, 
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE key = ?
                """, (json.dumps(value), key))
                
                if cursor.rowcount == 0:
                    # If no rows updated, insert new
                    await db.execute("""
                        INSERT INTO memory_store (key, value, category)
                        VALUES (?, ?, ?)
                    """, (key, json.dumps(value), category))
                
                await db.commit()
                logger.debug(f"Saved memory: {key}")
                return True
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False
    
    async def get_memory(self, key: str) -> Optional[Any]:
        """Get from memory store.
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Update access count and time
                await db.execute("""
                    UPDATE memory_store 
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE key = ?
                """, (key,))
                
                cursor = await db.execute("""
                    SELECT value FROM memory_store WHERE key = ?
                """, (key,))
                row = await cursor.fetchone()
                
                await db.commit()
                
                if row:
                    return json.loads(row[0])
                return None
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None
    
    async def search_memory(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory store.
        
        Args:
            category: Optional category filter
            limit: Maximum results
            
        Returns:
            List of memory items
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if category:
                    cursor = await db.execute("""
                        SELECT key, value, category, access_count, last_accessed
                        FROM memory_store
                        WHERE category = ?
                        ORDER BY last_accessed DESC
                        LIMIT ?
                    """, (category, limit))
                else:
                    cursor = await db.execute("""
                        SELECT key, value, category, access_count, last_accessed
                        FROM memory_store
                        ORDER BY last_accessed DESC
                        LIMIT ?
                    """, (limit,))
                
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "key": row[0],
                        "value": json.loads(row[1]),
                        "category": row[2],
                        "access_count": row[3],
                        "last_accessed": row[4]
                    })
                return results
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    # Research Reports
    
    async def save_research_report(self, report_id: str, plan_id: str, 
                                  query: str, report: str, cited_report: str,
                                  sources: List[Dict], metrics: Dict) -> bool:
        """Save final research report.
        
        Args:
            report_id: Report ID
            plan_id: Associated plan ID
            query: Original query
            report: Plain text report
            cited_report: Report with citations
            sources: List of sources
            metrics: Performance metrics
            
        Returns:
            Success status
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO research_reports 
                    (id, plan_id, query, report, cited_report, sources, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id,
                    plan_id,
                    query,
                    report,
                    cited_report,
                    json.dumps(sources),
                    json.dumps(metrics)
                ))
                await db.commit()
                logger.info(f"Saved research report: {report_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save research report: {e}")
            return False
    
    async def get_research_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get research report.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report data or None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT query, report, cited_report, sources, metrics, created_at
                    FROM research_reports
                    WHERE id = ?
                """, (report_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "query": row[0],
                        "report": row[1],
                        "cited_report": row[2],
                        "sources": json.loads(row[3]),
                        "metrics": json.loads(row[4]),
                        "created_at": row[5]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get research report: {e}")
            return None
    
    async def list_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent research reports.
        
        Args:
            limit: Maximum number of reports
            
        Returns:
            List of report summaries
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, query, created_at
                    FROM research_reports
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                rows = await cursor.fetchall()
                
                reports = []
                for row in rows:
                    reports.append({
                        "id": row[0],
                        "query": row[1],
                        "created_at": row[2]
                    })
                return reports
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []