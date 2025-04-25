from dooit.api.workspace import Workspace
from tests.test_core.core_base import CoreTestBase


class TestModel(CoreTestBase):
    # Using Workspace as an example because Model is an abstract class

    def test_creation_and_deletion(self):
        w = Workspace()
        w.save()
        assert len(Workspace.all()) == 1

        w.drop()
        assert len(Workspace.all()) == 0

    def test_shifts_normal(self):
        for _ in range(5):
            w = Workspace()
            w.save()

        workspace = Workspace.all()[0]

        assert workspace is not None

        siblings = workspace.siblings
        assert workspace.is_first_sibling()

        workspace.shift_down()
        siblings = workspace.siblings
        assert siblings[1].id == workspace.id

        workspace.shift_up()
        siblings = workspace.siblings
        assert siblings[0].id == workspace.id
        assert workspace.is_first_sibling()

    def test_shifts_edge(self):
        for _ in range(5):
            w = Workspace()
            w.save()

        workspaces = Workspace.all()

        assert not workspaces[0].shift_up()
        assert not workspaces[-1].shift_down()

    def test_sort_field(self):
        names = ["a", "b", "c", "d", "e"]
        workspaces = [Workspace(description=name) for name in names]
        w = workspaces[0]

        for i in reversed(workspaces):
            i.save()

        assert [i.description for i in w.siblings] == names[::-1]
        w.sort_siblings("description")
        assert [i.description for i in w.siblings] == names

    def test_sort_reverse(self):
        names = ["a", "b", "c", "d", "e"]
        workspaces = [Workspace(description=name) for name in names]
        w = workspaces[0]

        for i in reversed(workspaces):
            i.save()

        assert [i.description for i in w.siblings] == names[::-1]
        w.reverse_siblings()
        assert [i.description for i in w.siblings] == names
