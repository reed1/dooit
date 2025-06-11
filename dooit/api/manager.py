import os
from typing import Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from ._vars import DATABASE_CONN_STRING, DATABASE_SCHEMA


class Manager:
    """
    Class for managing sqlalchemy sessions
    """

    def connect(self, path: Optional[str] = None):
        """
        Connect to database using a file path

        Args:
            path: Path to SQLite database file. Can include ~ for home directory.
        """

        from dooit.api import BaseModel

        self.engine = create_engine(DATABASE_CONN_STRING)
        self.session = Session(self.engine)

        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()
        has_todo_table_initially = "todo" in existing_tables

        BaseModel.metadata.create_all(bind=self.engine)
        if not has_todo_table_initially:
            self.create_triggers()
        self._db_last_modified = self._get_db_last_modified()

    def _get_db_last_modified(self) -> Optional[float]:
        database = self.engine.url.database
        assert database is not None

        try:
            return os.path.getmtime(database)
        except OSError:
            return None

    def has_changed(self) -> bool:
        current_last_modified = self._get_db_last_modified()
        if current_last_modified and self._db_last_modified != current_last_modified:
            self._db_last_modified = current_last_modified
            manager.session.expire_all()
            return True
        return False

    def delete(self, obj):
        self.session.delete(obj)
        self.commit()

    def save(self, obj):
        self.session.add(obj)
        self.commit()

    def commit(self):
        self.session.commit()
        self._db_last_modified = self._get_db_last_modified()

    def create_triggers(self):
        schema_name = DATABASE_SCHEMA
        for table_name in ["todo", "workspace"]:
            self.session.execute(
                text(
                    f"""
            CREATE TRIGGER trg_log_crud_{schema_name}_{table_name}
            AFTER INSERT OR UPDATE OR DELETE ON {schema_name}.{table_name}
            FOR EACH ROW
            EXECUTE FUNCTION public.log_crud_operation();
            """
                )
            )


manager = Manager()
