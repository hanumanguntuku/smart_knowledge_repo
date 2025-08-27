"""
Database migration management for the Smart Knowledge Repository.

Handles database schema creation, updates, and data migrations.
"""

import os
import logging
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from .models import Base, DatabaseManager

class DatabaseMigrations:
    """Database migration management system."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.migrations_table = 'schema_migrations'
    
    def initialize_database(self):
        """Initialize the database with all tables."""
        try:
            # Create the data directory if it doesn't exist
            os.makedirs(os.path.dirname('data/profiles.db'), exist_ok=True)
            
            # Create all tables
            self.db_manager.create_tables()
            
            # Create migrations tracking table
            self._create_migrations_table()
            
            # Run initial migrations
            self._run_initial_migrations()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def _create_migrations_table(self):
        """Create table to track applied migrations."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        with self.db_manager.engine.begin() as conn:
            conn.execute(text(create_table_sql))
    
    def _run_initial_migrations(self):
        """Run initial database migrations."""
        initial_migrations = [
            {
                'version': '001_initial_schema',
                'description': 'Create initial tables for profiles and knowledge',
                'sql': self._get_initial_schema_sql()
            },
            {
                'version': '002_full_text_search',
                'description': 'Add full-text search capabilities',
                'sql': self._get_fts_sql()
            },
            {
                'version': '003_indexes',
                'description': 'Add performance indexes',
                'sql': self._get_indexes_sql()
            }
        ]
        
        for migration in initial_migrations:
            if not self._is_migration_applied(migration['version']):
                self._apply_migration(migration)
    
    def _get_initial_schema_sql(self) -> List[str]:
        """Get SQL for initial schema creation."""
        return [
            # Additional indexes and constraints not covered by SQLAlchemy
            "CREATE INDEX IF NOT EXISTS idx_profiles_name_fts ON profiles(name);",
            "CREATE INDEX IF NOT EXISTS idx_profiles_role_dept ON profiles(role, department);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_content_type ON knowledge_entries(content_type);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_profile ON knowledge_entries(profile_id);",
            "CREATE INDEX IF NOT EXISTS idx_search_knowledge ON search_indexes(knowledge_entry_id);"
        ]
    
    def _get_fts_sql(self) -> List[str]:
        """Get SQL for full-text search setup."""
        return [
            # Create FTS virtual table for profiles
            """CREATE VIRTUAL TABLE IF NOT EXISTS profiles_fts USING fts5(
                name, role, department, bio, 
                content='profiles', content_rowid='id'
            );""",
            
            # Create FTS virtual table for knowledge entries
            """CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                title, content, 
                content='knowledge_entries', content_rowid='id'
            );""",
            
            # Populate FTS tables
            "INSERT OR IGNORE INTO profiles_fts(profiles_fts) VALUES('rebuild');",
            "INSERT OR IGNORE INTO knowledge_fts(knowledge_fts) VALUES('rebuild');"
        ]
    
    def _get_indexes_sql(self) -> List[str]:
        """Get SQL for performance indexes."""
        return [
            # Additional performance indexes
            "CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_profiles_updated_at ON profiles(updated_at);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge_entries(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_updated_at ON knowledge_entries(updated_at);",
            "CREATE INDEX IF NOT EXISTS idx_search_queries_created_at ON search_queries(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_search_queries_query_type ON search_queries(query_type);"
        ]
    
    def _is_migration_applied(self, version: str) -> bool:
        """Check if a migration has been applied."""
        check_sql = f"SELECT COUNT(*) FROM {self.migrations_table} WHERE version = :version"
        
        with self.db_manager.engine.begin() as conn:
            result = conn.execute(text(check_sql), {'version': version})
            return result.scalar() > 0
    
    def _apply_migration(self, migration: Dict[str, Any]):
        """Apply a single migration."""
        try:
            with self.db_manager.engine.begin() as conn:
                # Execute migration SQL
                for sql_statement in migration['sql']:
                    if sql_statement.strip():
                        conn.execute(text(sql_statement))
                
                # Record migration as applied
                record_sql = f"""
                INSERT INTO {self.migrations_table} (version, description) 
                VALUES (:version, :description)
                """
                conn.execute(text(record_sql), {
                    'version': migration['version'],
                    'description': migration['description']
                })
            
            self.logger.info(f"Applied migration: {migration['version']}")
            
        except Exception as e:
            self.logger.error(f"Error applying migration {migration['version']}: {e}")
            raise
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations."""
        select_sql = f"""
        SELECT version, description, applied_at 
        FROM {self.migrations_table} 
        ORDER BY applied_at
        """
        
        with self.db_manager.engine.begin() as conn:
            result = conn.execute(text(select_sql))
            return [
                {
                    'version': row[0],
                    'description': row[1],
                    'applied_at': row[2]
                }
                for row in result.fetchall()
            ]
    
    def create_backup(self, backup_path: str):
        """Create a backup of the database."""
        try:
            import shutil
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy database file
            db_file = self.db_manager.database_url.replace('sqlite:///', '')
            if os.path.exists(db_file):
                shutil.copy2(db_file, backup_path)
                self.logger.info(f"Database backed up to: {backup_path}")
            else:
                raise FileNotFoundError(f"Database file not found: {db_file}")
                
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str):
        """Restore database from backup."""
        try:
            import shutil
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Close existing connections
            self.db_manager.engine.dispose()
            
            # Restore database file
            db_file = self.db_manager.database_url.replace('sqlite:///', '')
            shutil.copy2(backup_path, db_file)
            
            # Recreate engine
            self.db_manager.engine = create_engine(self.db_manager.database_url, echo=False)
            
            self.logger.info(f"Database restored from: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            raise
    
    def reset_database(self):
        """Reset database (drop and recreate all tables)."""
        try:
            self.logger.warning("Resetting database - all data will be lost!")
            
            # Drop all tables
            self.db_manager.drop_tables()
            
            # Recreate tables
            self.initialize_database()
            
            self.logger.info("Database reset completed")
            
        except Exception as e:
            self.logger.error(f"Error resetting database: {e}")
            raise
    
    def optimize_database(self):
        """Optimize database performance."""
        optimization_sql = [
            "VACUUM;",  # Rebuild database file
            "ANALYZE;",  # Update query planner statistics
            "PRAGMA optimize;",  # Run built-in optimizations
        ]
        
        try:
            with self.db_manager.engine.begin() as conn:
                for sql in optimization_sql:
                    conn.execute(text(sql))
            
            self.logger.info("Database optimization completed")
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats_sql = [
            "SELECT COUNT(*) FROM profiles;",
            "SELECT COUNT(*) FROM knowledge_entries;",
            "SELECT COUNT(*) FROM search_indexes;",
            "SELECT COUNT(*) FROM search_queries;",
            "PRAGMA page_count;",
            "PRAGMA page_size;",
            "PRAGMA freelist_count;"
        ]
        
        try:
            stats = {}
            with self.db_manager.engine.begin() as conn:
                stats['profile_count'] = conn.execute(text(stats_sql[0])).scalar()
                stats['knowledge_count'] = conn.execute(text(stats_sql[1])).scalar()
                stats['index_count'] = conn.execute(text(stats_sql[2])).scalar()
                stats['query_count'] = conn.execute(text(stats_sql[3])).scalar()
                
                page_count = conn.execute(text(stats_sql[4])).scalar()
                page_size = conn.execute(text(stats_sql[5])).scalar()
                freelist_count = conn.execute(text(stats_sql[6])).scalar()
                
                stats['database_size_bytes'] = page_count * page_size
                stats['free_space_bytes'] = freelist_count * page_size
                stats['utilization_percent'] = ((page_count - freelist_count) / page_count * 100) if page_count > 0 else 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
