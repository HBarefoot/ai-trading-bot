"""
Enhanced Alert System for Trading Bot
Real-time notifications and persistent alert storage
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AlertManager:
    """Manage persistent alerts with database storage"""
    
    def __init__(self, db_path: str = "data/alerts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize alerts database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT NOT NULL,
                data TEXT,
                read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON alerts(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol ON alerts(symbol)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_read ON alerts(read)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Alert database initialized: {self.db_path}")
    
    def add_alert(self, alert_type: str, symbol: str, message: str, 
                  priority: str = "INFO", data: Dict = None) -> int:
        """Add new alert to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data) if data else None
        
        cursor.execute("""
            INSERT INTO alerts (timestamp, alert_type, symbol, message, priority, data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, alert_type, symbol, message, priority, data_json))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Alert added: {alert_type} - {symbol} - {message}")
        return alert_id
    
    def get_alerts(self, limit: int = 50, offset: int = 0, 
                   symbol: Optional[str] = None,
                   alert_type: Optional[str] = None,
                   unread_only: bool = False,
                   hours: Optional[int] = None) -> List[Dict]:
        """Get alerts with filters"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        
        if unread_only:
            query += " AND read = 0"
        
        if hours:
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        alerts = []
        for row in rows:
            alert = dict(row)
            if alert['data']:
                alert['data'] = json.loads(alert['data'])
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def get_unread_count(self, symbol: Optional[str] = None) -> int:
        """Get count of unread alerts"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM alerts WHERE read = 0"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def mark_as_read(self, alert_id: int):
        """Mark alert as read"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts SET read = 1 WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()
    
    def mark_all_as_read(self, symbol: Optional[str] = None):
        """Mark all alerts as read"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute("UPDATE alerts SET read = 1 WHERE symbol = ?", (symbol,))
        else:
            cursor.execute("UPDATE alerts SET read = 1")
        
        conn.commit()
        conn.close()
    
    def delete_old_alerts(self, days: int = 30):
        """Delete alerts older than specified days"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            DELETE FROM alerts WHERE timestamp < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted} alerts older than {days} days")
        return deleted
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        
        # Unread alerts
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE read = 0")
        unread = cursor.fetchone()[0]
        
        # By priority
        cursor.execute("""
            SELECT priority, COUNT(*) as count 
            FROM alerts 
            GROUP BY priority
        """)
        by_priority = dict(cursor.fetchall())
        
        # By type
        cursor.execute("""
            SELECT alert_type, COUNT(*) as count 
            FROM alerts 
            GROUP BY alert_type
        """)
        by_type = dict(cursor.fetchall())
        
        # Recent (last 24 hours)
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp >= ?", (cutoff,))
        recent_24h = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_priority': by_priority,
            'by_type': by_type,
            'recent_24h': recent_24h
        }


# Singleton instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get singleton alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
