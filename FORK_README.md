# Fork Changes

Personal fork of [dooit](https://github.com/kraanzu/dooit) with modifications for multi-project support.

## Multi-Tenant Database

Tables are namespaced per project using `PROJECT_ID` environment variable:
- Table names: `dooit_{PROJECT_ID}_workspace`, `dooit_{PROJECT_ID}_todo`
- Requires environment variables: `DATABASE_CONN_STRING`, `PROJECT_ID`, `LIBSQL_SYNC_URL`, `LIBSQL_AUTH_TOKEN`

## TodoRegistry

Global registry table (`dooit_todo_registry`) that tracks todos across all projects:
- Syncs on todo create/update/delete via SQLAlchemy event listeners
- Enables cross-project todo search
- Fields: `project_id`, `workspace_id`, `todo_id`, `workspace_name`, `todo_name`, `created_at`, `updated_at`

## CLI

- `--init-db` flag to initialize database tables and exit

## API Additions

- `remove_node_no_confirm()` - Delete without confirmation dialog
- `copy_and_remove_node()` - Copy description then delete
- `move_to_top()` / `move_to_bottom()` - Reorder items
- `add_sibling_before()` - Add sibling above current item
- `add_sibling_from_clipboard()` - Add sibling with description from clipboard
- `add_task_at_bottom()` - Add task at end of list
- Add "RECORDING" mode onto enum ModeType

## Bug Fixes

- `add_sibling` handles empty list or no highlighted item
