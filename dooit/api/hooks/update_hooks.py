from datetime import datetime
from sqlalchemy import event, update
from ..todo import Todo


@event.listens_for(Todo, "before_update")
def update_children_to_pending(_, connection, target: Todo):
    if not target.pending:
        return
        
    to_update = []

    def update_children(todo: Todo):
        for child in todo.todos:
            to_update.append(child.id)
            update_children(child)

    update_children(target)
    query = update(Todo).where(Todo.id.in_(to_update)).values(pending=True)
    connection.execute(query)


@event.listens_for(Todo, "before_update")
def update_children_to_completed(_, connection, target: Todo):
    if target.pending:
        return
        
    to_update = []

    def update_children(todo: Todo):
        for child in todo.todos:
            to_update.append(child.id)
            update_children(child)

    update_children(target)
    query = update(Todo).where(Todo.id.in_(to_update)).values(pending=False)
    connection.execute(query)


@event.listens_for(Todo, "before_update")
def update_parent_to_pending(mapper, connection, target: Todo):
    if not target.pending:
        return
        
    to_update = []

    def update_parent_pending(todo: Todo):
        parent = todo.parent_todo
        if not parent:
            return

        to_update.append(parent.id)
        update_parent_pending(parent)

    update_parent_pending(target)
    query = update(Todo).where(Todo.id.in_(to_update)).values(pending=True)
    connection.execute(query)


@event.listens_for(Todo, "before_update") 
def update_parent_to_completed(mapper, connection, target: Todo):
    if target.pending:
        return
        
    to_update = []

    def update_parent_completed(todo: Todo):
        parent = todo.parent_todo
        if not parent:
            return

        all_sibling_completed = all([not sibling.pending for sibling in parent.todos])
        if all_sibling_completed:
            parent.pending = False
            to_update.append(parent.id)
            update_parent_completed(parent)

    update_parent_completed(target)
    query = update(Todo).where(Todo.id.in_(to_update)).values(pending=False)
    connection.execute(query)


@event.listens_for(Todo, "before_update")
def update_due_for_recurrence(mapper, connection, todo: Todo):
    if todo.recurrence is None:
        return

    if todo.due is None:
        todo.due = datetime.now()

    if todo.pending:
        return

    todo.pending = True
    todo.due += todo.recurrence
