from typing import TYPE_CHECKING
from textual.widgets import ContentSwitcher
from dooit.ui.api.events import BarNotification, NotificationType
from dooit.ui.api.plug import PluginManager
from .events import DooitEvent, SwitchTab, QuitApp
from dooit.ui.widgets import ModelTree
from dooit.ui.widgets.trees import TodosTree
from dooit.utils import CssManager

from .api_components import (
    KeyManager,
    KeyMatchType,
    LayoutManager,
    Formatter,
    BarManager,
    VarManager,
    DashboardManager,
)

if TYPE_CHECKING:  # pragma: no cover
    from ..tui import Dooit


class DooitAPI:
    def __init__(
        self,
        app: "Dooit",
    ) -> None:
        self.app = app
        self.plugin_manager = PluginManager(self, app.config)
        self.css = CssManager()
        self.keys = KeyManager(self.app.get_dooit_mode)
        self.layouts = LayoutManager(self.app)
        self.formatter = Formatter(self)
        self.bar = BarManager(self)
        self.vars = VarManager(self)
        self.dashboard = DashboardManager(self.app)

        self.css.refresh_css()

    def no_op(self):
        """<NOP>"""
        pass

    def quit(self):
        """Quit dooit"""
        self.app.post_message(QuitApp())

    def notify(self, message: str, level: NotificationType = "info") -> None:
        self.app.bar_switcher.switch_to_notification(BarNotification(message, level))

    async def handle_key(self, key: str) -> None:
        keymatch = self.keys.register_key(key)

        if keymatch.match_type == KeyMatchType.NoMatchFound:
            await self.focused.handle_keypress(key)
            return

        if keymatch.match_type == KeyMatchType.MultipleMatchFound:
            return

        assert keymatch.function is not None
        try:
            keymatch.function.callback()
        except Exception as e:
            self.app.bar_switcher.switch_to_notification(
                BarNotification(str(e), "error")
            )

    def trigger_event(self, event: DooitEvent):
        self.plugin_manager.on_event(event)

    # -----------------------------------------

    @property
    def focused(self) -> ModelTree:
        focused = self.app.focused
        if isinstance(focused, ModelTree):
            return focused

        raise ValueError(f"Expected BaseTree, got {type(focused)}")

    def copy_description_to_clipboard(self):
        """Copy the description of the focused item to the clipboard"""

        self.focused.copy_description_to_clipboard()

    def switch_focus(self):
        """Switch focus between the workspace and the todo list"""

        if self.app.bar_switcher.is_focused:
            return

        if w := self.app.focused:
            w.post_message(SwitchTab())

    def move_down(self):
        """Move the cursor down in the focused list"""

        self.focused.action_cursor_down()

    def move_up(self):
        """Move the cursor up in the focused list"""

        self.focused.action_cursor_up()

    def shift_up(self):
        """Shift the highlighted item up"""

        self.focused.shift_up()

    def shift_down(self):
        """Shift the highlighted item down"""

        self.focused.shift_down()

    def go_to_top(self):
        """Move the cursor to the top of the list"""
        self.focused.action_first()

    def go_to_bottom(self):
        """Move the cursor to the bottom of the list"""
        self.focused.action_last()

    def edit(self, property: str):
        """Start editing a property of the focused item"""
        self.focused.start_edit(property)

    def edit_description(self):
        """Start editing the description of the focused item"""
        return self.edit("description")

    def edit_due(self):
        """Start editing the due date of the todo"""
        return self.edit("due")

    def edit_recurrence(self):
        """Start editing the recurrence of the todo"""
        return self.edit("recurrence")

    def edit_effort(self):
        return self.edit("effort")

    def add_sibling(self):
        """Add a sibling to highlighted item"""
        self.focused.add_sibling()

    def add_sibling_from_clipboard(self):
        """Add a sibling to highlighted item and set its description from clipboard"""
        self.focused.add_sibling_from_clipboard()

    def add_sibling_before(self):
        """Add a sibling before the highlighted item"""
        self.focused.add_sibling_before()

    def toggle_expand(self):
        """Toggle the expansion of the highlighted item"""
        self.focused.toggle_expand()

    def toggle_expand_parent(self):
        """Toggle the expansion of the parent of the highlighted item"""
        self.focused.toggle_expand_parent()

    def add_child_node(self):
        """Add a child to the highlighted item"""
        self.focused.add_child_node()

    def remove_node(self):
        """Remove the highlighted item"""
        self.focused.remove_node()

    def copy_and_remove_node(self):
        """Copy node description and remove the node"""
        self.focused.copy_description_to_clipboard()
        self.focused.remove_node()

    def start_search(self):
        """Start a search within the list"""
        self.focused.start_search()

    def start_sort(self):
        """Start sorting the siblings of the highlighted item"""
        self.focused.start_sort()

    def toggle_complete(self):
        """Toggle the completion of the todo"""
        if isinstance(self.focused, TodosTree):
            self.focused.toggle_complete()

    def add_task_at_bottom(self):
        """Add a new task at the bottom of the list. If focus is not on TodosTree, switch to it first."""
        if not isinstance(self.focused, TodosTree):
            self.app.action_focus_next()
        if not isinstance(self.focused, TodosTree):
            return
        if self.focused.option_count == 0:
            self.focused.add_first_item()
        else:
            self.focused.action_last()
            self.focused.add_sibling()

    def increase_urgency(self):
        """Increase the urgency of the todo"""
        if isinstance(self.focused, TodosTree):
            self.focused.increase_urgency()

    def decrease_urgency(self):
        """Decrease the urgency of the todo"""
        if isinstance(self.focused, TodosTree):
            self.focused.decrease_urgency()

    def move_to_delay_workspace(self):
        """Move the highlighted todo to the DELAY workspace"""
        if not isinstance(self.focused, TodosTree):
            raise ValueError("Must be focusing on a todo to move to delay workspace")

        if self.focused.highlighted is None:
            raise ValueError("No todo is currently highlighted")

        todo = self.focused.current_model
        todo.move_to_delay_workspace()
        self.focused.force_refresh()

    def force_refresh(self):
        """Force a refresh of the focused tree"""
        self.focused.force_refresh()

    def show_help(self):
        """Show the help screen"""
        self.focused.show_help()
