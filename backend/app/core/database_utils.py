"""
Database utility functions for connection management and operations
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from contextlib import contextmanager
from typing import Generator, Optional, Any, Dict, List
import logging

from app.core.database import SessionLocal, engine
from app.models.base import Base

logger = logging.getLogger(__name__)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_all_tables() -> None:
    """
    Create all database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def drop_all_tables() -> None:
    """
    Drop all database tables
    WARNING: This will delete all data!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise

def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_table_info() -> Dict[str, Any]:
    """
    Get information about database tables
    """
    try:
        with get_db_session() as db:
            # Get table names
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            # Get table counts
            table_counts = {}
            for table in tables:
                try:
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    table_counts[table] = count_result.scalar()
                except Exception as e:
                    logger.warning(f"Could not get count for table {table}: {e}")
                    table_counts[table] = "Error"
            
            return {
                "tables": tables,
                "table_counts": table_counts,
                "total_tables": len(tables)
            }
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        return {"error": str(e)}

def execute_raw_sql(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute raw SQL query and return results
    WARNING: Use with caution, prefer ORM methods
    """
    try:
        with get_db_session() as db:
            result = db.execute(sql, params or {})
            if result.returns_rows:
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                return [{"affected_rows": result.rowcount}]
    except Exception as e:
        logger.error(f"Error executing raw SQL: {e}")
        raise

class DatabaseHealthCheck:
    """
    Database health check utilities
    """
    
    @staticmethod
    def check_connection() -> Dict[str, Any]:
        """
        Comprehensive database health check
        """
        health_status = {
            "status": "unknown",
            "connection": False,
            "tables_exist": False,
            "can_query": False,
            "details": {}
        }
        
        try:
            # Test basic connection
            with get_db_session() as db:
                db.execute(text("SELECT 1"))
                health_status["connection"] = True
                
                # Check if tables exist
                result = db.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.scalar()
                health_status["tables_exist"] = table_count > 0
                health_status["details"]["table_count"] = table_count
                
                # Test query performance
                import time
                start_time = time.time()
                db.execute(text("SELECT NOW()"))
                query_time = time.time() - start_time
                health_status["can_query"] = True
                health_status["details"]["query_time_ms"] = round(query_time * 1000, 2)
                
                # Overall status
                if health_status["connection"] and health_status["can_query"]:
                    health_status["status"] = "healthy"
                else:
                    health_status["status"] = "degraded"
                    
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["details"]["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health_status