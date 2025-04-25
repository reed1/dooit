from dooit.api import Workspace
from tests.test_core.core_base import *  # noqa


def test_workspace_creation(create_workspace):
    _ = [create_workspace() for _ in range(5)]
    assert len(Workspace.all()) == 5


def test_siblings_by_creation(create_workspace):
    workspace = [create_workspace() for _ in range(5)][0]
    assert len(workspace.siblings) == 5


def test_sibling_methods(create_workspace):
    workspace = [create_workspace() for _ in range(5)][0]
    siblings = workspace.siblings
    index_ids = [w.order_index for w in siblings]

    assert siblings[0].is_first_sibling()
    assert siblings[-1].is_last_sibling()
    assert index_ids == [0, 1, 2, 3, 4]


def test_parent_kind(create_workspace):
    workspace1 = create_workspace()
    workspace2 = create_workspace(parent_workspace=workspace1)

    assert workspace2.has_same_parent_kind


def test_sibling_add(create_workspace):
    w1 = create_workspace()

    w1.add_sibling()
    w2 = w1.add_sibling()

    assert len(w1.siblings) == 3
    assert len(w2.siblings) == 3
    assert w2.order_index == 1


def test_workspace_add(create_workspace):
    super_w = create_workspace()

    super_w.add_workspace()
    w = super_w.add_workspace()

    assert len(w.siblings) == 2
    assert w.order_index == 1


def test_todo_add(create_workspace):
    super_w = create_workspace()

    super_w.add_todo()
    todo = super_w.add_todo()

    assert len(todo.siblings) == 2
    assert todo.order_index == 1


def test_comparable_fields():
    fields = Workspace.comparable_fields()
    expected_fields = ["description"]
    assert fields == expected_fields


def test_nest_level(create_workspace):
    w = create_workspace()
    assert w.nest_level == 0

    w = w.add_workspace()
    assert w.nest_level == 1

    w = w.add_workspace()
    assert w.nest_level == 2


def test_root():
    assert len(Workspace.all()) == 0
