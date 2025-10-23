import os
from sqlalchemy import event, text
from sqlalchemy.orm import Session


def get_root_workspace(todo):
    """
    Traverse from a Todo to find its root workspace.

    If the todo has a parent_workspace, return it.
    If the todo has a parent_todo, traverse up the chain until we find a workspace.
    """
    if todo.parent_workspace:
        return todo.parent_workspace

    current_todo = todo.parent_todo
    while current_todo:
        if current_todo.parent_workspace:
            return current_todo.parent_workspace
        current_todo = current_todo.parent_todo

    return None


@event.listens_for(Session, "after_flush")
def sync_todo_registry(session, flush_context):
    """
    Synchronize TodoRegistry after any flush operation.
    Handles inserts, updates, and deletes for Todo objects.
    """
    from dooit.api.todo import Todo, TodoRegistry

    project_id = os.getenv("PROJECT_ID", "default")

    for obj in session.new:
        if isinstance(obj, Todo):
            workspace = get_root_workspace(obj)
            if workspace:
                registry_entry = TodoRegistry(
                    project_id=project_id,
                    workspace_id=workspace.id,
                    todo_id=obj.id,
                    workspace_name=workspace.description,
                    todo_name=obj.description,
                )
                session.add(registry_entry)

    for obj in session.dirty:
        if isinstance(obj, Todo) and session.is_modified(obj):
            workspace = get_root_workspace(obj)
            if workspace:
                stmt = text(
                    """
                    UPDATE dooit_todo_registry
                    SET workspace_id = :workspace_id,
                        workspace_name = :workspace_name,
                        todo_name = :todo_name,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = :project_id AND todo_id = :todo_id
                """
                )
                session.execute(
                    stmt,
                    {
                        "workspace_id": workspace.id,
                        "workspace_name": workspace.description,
                        "todo_name": obj.description,
                        "project_id": project_id,
                        "todo_id": obj.id,
                    },
                )

    for obj in session.deleted:
        if isinstance(obj, Todo):
            stmt = text(
                """
                DELETE FROM dooit_todo_registry
                WHERE project_id = :project_id AND todo_id = :todo_id
            """
            )
            session.execute(
                stmt,
                {
                    "project_id": project_id,
                    "todo_id": obj.id,
                },
            )
