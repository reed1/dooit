from typing import TYPE_CHECKING, Optional, Union
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import ForeignKey, select, nulls_last
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from .model import DooitModel
from .manager import manager

if TYPE_CHECKING:  # pragma: no cover
    from dooit.api.workspace import Workspace


class Todo(DooitModel):
    # id: Mapped[int] = mapped_column(primary_key=True, default=generate_unique_id)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_index: Mapped[int] = mapped_column(default=-1)
    description: Mapped[str] = mapped_column(default="")
    due: Mapped[Optional[datetime]] = mapped_column(default=None)
    effort: Mapped[int] = mapped_column(default=0)
    recurrence: Mapped[Optional[timedelta]] = mapped_column(default=None)
    urgency: Mapped[int] = mapped_column(default=1)
    pending: Mapped[bool] = mapped_column(default=True)

    # --------------------------------------------------------------
    # ------------------- Relationships ----------------------------
    # --------------------------------------------------------------

    parent_workspace_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workspace.id")
    )
    parent_workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace",
        back_populates="todos",
    )

    parent_todo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("todo.id"))
    parent_todo: Mapped[Optional["Todo"]] = relationship(
        "Todo",
        back_populates="todos",
        remote_side=[id],
    )

    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        back_populates="parent_todo",
        cascade="all, delete-orphan",
        order_by=order_index,
    )

    @validates("recurrence")
    def validate_pending(self, key, value):
        if value is not None:
            self.pending = True

        return value

    @classmethod
    def from_id(cls, _id: str) -> "Todo":
        _id = _id.lstrip("Todo_")
        query = select(Todo).where(Todo.id == int(_id))
        res = manager.session.execute(query).scalars().first()
        assert res is not None
        return res

    @property
    def parent(self) -> Union["Workspace", "Todo"]:
        assert self.parent_workspace or self.parent_todo

        if self.parent_workspace:
            return self.parent_workspace

        assert self.parent_todo is not None

        return self.parent_todo

    @property
    def has_same_parent_kind(self) -> bool:
        return self.parent_todo is not None

    @property
    def tags(self) -> List[str]:
        return [i for i in self.description.split() if i[0] == "@"]

    @property
    def status(self) -> str:
        if self.is_completed:
            return "completed"

        if self.is_overdue:
            return "overdue"

        return "pending"

    @property
    def siblings(self) -> List["Todo"]:
        if self.parent_workspace:
            return self.parent_workspace.todos

        if self.parent_todo:
            return self.parent_todo.todos

        return []

    def sort_siblings(self, field: str):
        if field != "pending":
            items = (
                self.session.query(Todo)
                .filter_by(
                    parent_workspace=self.parent_workspace,
                    parent_todo=self.parent_todo,
                )
                .order_by(nulls_last(getattr(Todo, field).asc()))
                .all()
            )
        else:
            items = sorted(
                self.siblings,
                key=lambda x: (
                    not x.pending,
                    x.due or datetime.max,
                    x.order_index,
                ),
            )

        for index, todo in enumerate(items):
            todo.order_index = index

        manager.commit()

    def add_todo(self) -> "Todo":
        todo = Todo(parent_todo=self)
        todo.save()
        return todo

    def _add_sibling(self) -> "Todo":
        todo = Todo(
            parent_todo=self.parent_todo,
            parent_workspace=self.parent_workspace,
            order_index=self.order_index + 1,
        )
        todo.save()
        return todo

    def move_to_workspace(self, target_workspace: "Workspace") -> None:
        """
        Move this todo to the specified workspace
        FIXME: After call, call `api.force_refresh` is still needed to refresh the workspace tree
        """
        if target_workspace is None:
            raise ValueError("Target workspace cannot be None")

        # Set new parent workspace and clear parent todo (if it was a subtodo)
        self.parent_workspace = target_workspace
        self.parent_todo = None

        # Set order_index to append at the end of the new workspace's todos
        self.order_index = len(target_workspace.todos)
        self.save()

    def move_to_delay_workspace(self) -> None:
        """
        Move this todo to the DELAY workspace (creates it if it doesn't exist)
        FIXME: After call, call `api.force_refresh` is still needed to refresh the workspace tree
        """
        from .workspace import Workspace

        delay_workspace = Workspace.get_delay_workspace()
        self.move_to_workspace(delay_workspace)

    # ----------- HELPER FUNCTIONS --------------

    def increase_urgency(self) -> None:
        self.urgency += 1
        self.save()

    def decrease_urgency(self) -> None:
        self.urgency -= 1
        self.save()

    def toggle_complete(self) -> None:
        self.pending = not self.pending
        self.save()

    def is_due_today(self) -> bool:
        if not self.due:
            return False

        return self.due and self.due.day == datetime.today().day

    @property
    def is_completed(self) -> bool:
        return self.pending == False

    @property
    def is_pending(self) -> bool:
        return self.pending

    @property
    def is_overdue(self) -> bool:
        if not self.due:
            return False

        return self.pending and self.due < datetime.now()

    @classmethod
    def all(cls) -> List["Todo"]:
        query = select(Todo)
        return list(manager.session.execute(query).scalars().all())
