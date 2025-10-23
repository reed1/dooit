from tests.test_core.core_base import *  # noqa
from dooit.api.todo import TodoRegistry
from sqlalchemy import select


def test_todo_status_update_children(todo1):
    assert todo1.is_pending

    for child_todo in todo1.todos:
        child_todo.toggle_complete()

    assert not todo1.is_pending


def test_todo_registry_insert(create_workspace, create_todo, session):
    workspace = create_workspace("Test Workspace")
    todo = create_todo("Test Todo", parent_workspace=workspace)

    query = select(TodoRegistry).where(TodoRegistry.todo_id == todo.id)
    registry_entry = session.execute(query).scalars().first()

    assert registry_entry is not None
    assert registry_entry.workspace_id == workspace.id
    assert registry_entry.workspace_name == "Test Workspace"
    assert registry_entry.todo_name == "Test Todo"


def test_todo_registry_update(create_workspace, create_todo, session):
    workspace = create_workspace("Original Workspace")
    todo = create_todo("Original Todo", parent_workspace=workspace)

    todo.description = "Updated Todo"
    todo.save()

    query = select(TodoRegistry).where(TodoRegistry.todo_id == todo.id)
    registry_entry = session.execute(query).scalars().first()

    assert registry_entry is not None
    assert registry_entry.todo_name == "Updated Todo"


def test_todo_registry_delete(create_workspace, create_todo, session):
    workspace = create_workspace("Test Workspace")
    todo = create_todo("Test Todo", parent_workspace=workspace)
    todo_id = todo.id

    todo.drop()

    query = select(TodoRegistry).where(TodoRegistry.todo_id == todo_id)
    registry_entry = session.execute(query).scalars().first()

    assert registry_entry is None


def test_todo_registry_with_parent_todo(create_workspace, create_todo, session):
    workspace = create_workspace("Test Workspace")
    parent_todo = create_todo("Parent Todo", parent_workspace=workspace)
    child_todo = create_todo("Child Todo", parent_todo=parent_todo)

    query = select(TodoRegistry).where(TodoRegistry.todo_id == child_todo.id)
    registry_entry = session.execute(query).scalars().first()

    assert registry_entry is not None
    assert registry_entry.workspace_id == workspace.id
    assert registry_entry.workspace_name == "Test Workspace"
    assert registry_entry.todo_name == "Child Todo"
