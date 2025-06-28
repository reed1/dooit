from typing import List, Optional, Union
from sqlalchemy import ForeignKey, asc, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..api.todo import Todo
from .model import DooitModel
from .manager import manager

ModelType = Union["Workspace", "Todo"]
ModelTypeList = Union[List["Workspace"], List["Todo"]]


class Workspace(DooitModel):
    # id: Mapped[int] = mapped_column(primary_key=True, default=generate_unique_id)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_index: Mapped[int] = mapped_column(default=-1)
    description: Mapped[str] = mapped_column(default="")
    is_root: Mapped[bool] = mapped_column(default=False)

    # --------------------------------------------------------------
    # ------------------- Relationships ----------------------------
    # --------------------------------------------------------------

    parent_workspace_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workspace.id"), default=None
    )
    parent_workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace",
        back_populates="workspaces",
        remote_side=[id],
    )

    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="parent_workspace",
        cascade="all",
        order_by="Workspace.order_index",
    )
    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        back_populates="parent_workspace",
        cascade="all, delete-orphan",
        order_by="Todo.order_index",
    )

    @classmethod
    def _get_or_create_root(cls) -> "Workspace":
        query = select(Workspace).where(Workspace.is_root == True)
        root = manager.session.execute(query).scalars().first()

        if root is None:
            root = Workspace(is_root=True)

        return root

    @classmethod
    def from_id(cls, _id: str) -> "Workspace":
        _id = _id.lstrip("Workspace_")
        query = select(Workspace).where(Workspace.id == int(_id))
        res = manager.session.execute(query).scalars().first()
        assert res is not None
        return res

    @property
    def parent(self) -> Optional["Workspace"]:
        return self.parent_workspace

    @property
    def has_same_parent_kind(self) -> bool:
        return self.parent is not None

    @property
    def siblings(self) -> List["Workspace"]:
        if not self.parent_workspace:
            return []

        assert not self.is_root

        return self.parent_workspace.workspaces

    def sort_siblings(self, field: str):
        items = (
            self.session.query(Workspace)
            .filter_by(
                parent_workspace=self.parent_workspace,
            )
            .order_by(asc(getattr(Workspace, field)))
            .all()
        )

        for index, workspace in enumerate(items):
            workspace.order_index = index

        manager.commit()

    def add_workspace(self) -> "Workspace":
        workspace = Workspace(parent_workspace=self)
        workspace.save()
        return workspace

    def add_todo(self) -> "Todo":
        todo = Todo(parent_workspace=self)
        todo.save()
        return todo

    def _add_sibling(self) -> "Workspace":
        workspace = Workspace(
            parent_workspace=self.parent_workspace,
            order_index=self.order_index + 1,
        )
        workspace.save()
        return workspace

    def save(self) -> None:
        if not self.parent_workspace and not self.is_root:
            root = self._get_or_create_root()
            self.parent_workspace = root

        return super().save()

    @classmethod
    def all(cls) -> List["Workspace"]:
        query = select(Workspace).where(Workspace.is_root == False)
        return list(manager.session.execute(query).scalars().all())

    @classmethod
    def get_delay_workspace(cls) -> "Workspace":
        """
        Get or create a root-level workspace with the name 'DELAY'

        Returns:
            The DELAY workspace (existing or newly created)
        """
        root = cls._get_or_create_root()

        # Look for existing DELAY workspace at root level
        for workspace in root.workspaces:
            if workspace.description == "DELAY":
                return workspace

        # Create new DELAY workspace if not found
        delay_workspace = Workspace(
            description="DELAY",
            parent_workspace=root
        )
        delay_workspace.save()
        return delay_workspace
