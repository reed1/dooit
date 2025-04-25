from typing import List, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select
from pytest import raises, mark
from dooit.api.exceptions import NoParentError, MultipleParentError
from tests.test_core.core_base import CoreTestBase
from dooit.api import Todo, Workspace


class TestTodo(CoreTestBase):
    def setUp(self):
        super().setUp()
        self.default_workspace = Workspace()

    def test_todo_creation(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        result = Todo.all()
        assert len(result) == 5

        indexs = sorted([t.order_index for t in result])
        assert indexs == [0, 1, 2, 3, 4]

    def test_sibling_methods(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        query = select(Todo)
        todo = self.session.execute(query).scalars().first()
        assert todo is not None

        siblings = todo.siblings
        index_ids = [w.order_index for w in siblings]
        assert index_ids == [0, 1, 2, 3, 4]
        assert siblings[0].is_first_sibling()
        assert siblings[-1].is_last_sibling()

    def test_todo_siblings_by_creation(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        query = select(Todo)
        workspace = self.session.execute(query).scalars().first()
        assert workspace is not None
        assert len(workspace.siblings) == 5

    def test_parent_kind(self):
        todo = Todo(parent_workspace=self.default_workspace)
        todo.save()
        assert not todo.has_same_parent_kind

        todo2 = Todo(parent_todo=todo)
        todo2.save()
        assert todo2.has_same_parent_kind

    def test_without_parent(self):
        todo = Todo()
        with raises(NoParentError):
            todo.save()

    def test_with_both_parents(self):
        w = self.default_workspace
        t = w.add_todo()
        todo = Todo(parent_workspace=w, parent_todo=t)
        with raises(MultipleParentError):
            todo.save()

    def test_sibling_add(self):
        t = self.default_workspace.add_todo()
        self.default_workspace.add_todo()
        t2 = t.add_sibling()
        assert len(t.siblings) == 3
        assert len(t2.siblings) == 3
        assert t2.order_index == 1

    def test_comparable_fields(self):
        fields = Todo.comparable_fields()
        expected_fields = [
            "description",
            "due",
            "effort",
            "recurrence",
            "urgency",
            "pending",
        ]
        assert fields == expected_fields

    def test_nest_level(self):
        t = self.default_workspace.add_todo()
        assert t.nest_level == 0

        t = t.add_todo()
        assert t.nest_level == 1

        t = t.add_todo()
        assert t.nest_level == 2

    def test_from_id(self):
        t = self.default_workspace.add_todo()
        _id = t.id
        t_from_id = Todo.from_id(str(_id))
        assert t_from_id == t

    def test_toggle_complete(self):
        t = self.default_workspace.add_todo()
        assert t.pending
        assert t.is_pending
        assert not t.is_completed

        t.toggle_complete()
        assert not t.pending
        assert not t.is_pending
        assert t.is_completed

    def test_toggle_complete_parent(self):
        t = self.default_workspace.add_todo()
        t1 = t.add_todo()
        t2 = t.add_todo()

        t1.toggle_complete()
        assert not t.is_completed

        t2.toggle_complete()
        assert t.is_completed

        t1.toggle_complete()
        assert not t.is_completed

    def test_due_date_util(self):
        t = self.default_workspace.add_todo()
        assert not t.due
        assert not t.is_overdue
        assert not t.is_due_today()
        assert t.status == "pending"

        t.due = datetime.now()
        assert t.is_overdue
        assert t.due
        assert t.is_due_today()
        assert t.status == "overdue"

        t.due = datetime.now() - timedelta(days=1)
        assert not t.is_due_today()
        assert t.is_overdue
        assert t.status == "overdue"

        t.due = datetime.now() + timedelta(days=1)
        assert not t.is_overdue
        assert t.status == "pending"

        t.toggle_complete()
        assert t.status == "completed"

    def test_tags(self):
        t = self.default_workspace.add_todo()
        t.description = "This is a @tag"
        assert t.tags == ["@tag"]

        t.description = "This is a @tag and @another"
        assert t.tags == ["@tag", "@another"]

        t.description = "This is a tag"
        assert t.tags == []

    def test_urgency(self):
        t = self.default_workspace.add_todo()
        assert t.urgency == 1

        t.decrease_urgency()
        assert t.urgency == 1

        t.increase_urgency()
        t.increase_urgency()
        t.increase_urgency()
        t.increase_urgency()
        t.increase_urgency()
        assert t.urgency == 4

    def test_recurrence_change(self):
        t = self.default_workspace.add_todo()
        t.due = datetime.strptime("2021-01-01", "%Y-%m-%d")
        t.recurrence = timedelta(days=1)
        t.save()
        assert t.due == datetime.strptime("2021-01-01", "%Y-%m-%d")
        t.toggle_complete()
        assert t.due == datetime.strptime("2021-01-02", "%Y-%m-%d")

    def test_sort_invalid(self):
        t = self.default_workspace.add_todo()
        with raises(AttributeError):
            t.sort_siblings("???????")

    def _sort_before_and_after(self, field) -> Tuple[List[Todo], List[Todo]]:
        from tests.generate_test_data import generate

        generate(self.session)
        w = Workspace.all()[2]
        t = w.todos[0]
        old_todos = t.siblings
        t.sort_siblings(field)
        new_descriptions = t.siblings
        return old_todos, new_descriptions

    @mark.parametrize(
        "field,sort_key,filter_func,compare_ids",
        [
            (
                "pending",
                lambda x: (not x.pending, x.due or datetime.max, x.order_index),
                None,
                True,
            ),
            ("description", lambda x: x.description, None, False),
            ("recurrence", lambda x: x.recurrence, lambda x: x.recurrence, False),
            ("effort", lambda x: x.effort, None, False),
            ("urgency", lambda x: x.urgency, None, False),
            ("due", lambda x: x.due, lambda x: x.due, True),
        ],
    )
    def test_sort(self, field, sort_key, filter_func, compare_ids):
        old, new = self._sort_before_and_after(field)

        if filter_func:
            old = [t for t in old if filter_func(t)]
            new = new[: len(old)]

        old.sort(key=sort_key)

        if compare_ids:
            assert [i.id for i in old] == [i.id for i in new]
        else:
            assert old == new
