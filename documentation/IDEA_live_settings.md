IDEA: apply settings without restarting the application
========================================================

Status: **idea, not scheduled** (analysed on 2026-10-22, to be taken up in the future).
Starting point: the Settings dialog with tabs (branch `feature/advanced-settings-tabs`).

## Root cause

Almost all the code reads the settings from `Config().app_settings`, the snapshot taken at
startup, while the Settings dialog stores the new values in `Config().app_settings_copy`.
A change is not noticed until restart even when the consumer reads the value every time it
uses it. Only the theme is applied live, through `ThemeService`.

## Settings that can be applied live with little effort

| Setting | Where it is read | What is needed |
|---|---|---|
| `edit_on_clone` | When an object is created (`main_menu.py`, `archetypes_menu_dropdown.py`) | Read the updated value |
| `developer_features` | Context menu, created on every right click (`context_menu.py`) | Read the updated value |
| `open_project_on_startup` | Only at startup (`app.py`) | Nothing: it already applies to the next startup, but today it shows the restart warning, which is misleading |
| `default_view` | When `ViewsContainer` is created, once per opened project (`views_container.py`) | Read the updated value; it applies when the next project is opened |
| `spellchecker_language` | `SpellCheckerWrapper` singleton, configured in `app.py` | Call `set_language()` on save and add a `disable()` method (it does not exist). The Settings dialog is modal, so no text editor is open meanwhile |
| `xslt_debug_mode` | `RenderService._get_xslt()`, decides whether templates are cached | Read the updated value and clear `_transformations` when it is turned on |

How to do it:

1. Split the settings in `SettingsDialog.save_button_clicked` into live ones (theme, the six
   above and MCP if done) and restart ones (language and profile: `selected_profile`,
   `using_default_profile`, `custom_profile_path`).
2. On save, also copy the live settings to `Config().app_settings`, as is done with the
   theme, so that consumers need no change.
3. Show the restart warning only when a restart setting changes, using an explicit list of
   fields instead of excluding the theme by hand.
4. Add an apply step (e.g. `_apply_live_settings()`) for the spellchecker and the XSLT cache.
5. Update the `settings_dialog.info.label` text.

## Medium effort: the MCP server

- Today the plugin only registers the component when `mcp_server_enabled` is true at plugin
  loading (`resources/plugins/proteus_mcp/__init__.py`); host and port are read in the
  constructor (`server.py`), and the server runs `FastMCP.run()` in a daemon thread that
  cannot be stopped (`_stop_server` has a `TODO`).
- Needed: always register the component and keep it idle; run the server with an own
  `uvicorn.Server` over the FastMCP HTTP app so that it can be stopped with `should_exit`;
  offer `start()`, `stop()` and `restart(host, port)`, called from the dialog on save.
- Risks: busy port (warn the user); restarting drops the sessions of connected clients; the
  dialog (core) must talk to a plugin component, better through an event than an import.

## Settings that still need a restart

- **Language:** almost every UI text is set with `_()` when each widget is built, so a live
  change would require rebuilding the main window. The language also selects the profile
  archetypes and i18n (`ProfileSettings.load(path, language)` in `config.py`) and the
  variant of each XSLT template (`render_service.py`).
- **Profile:** `Config().profile_settings` is loaded at startup together with archetypes,
  XSLT templates, icons, translations and profile plugins, and loaded plugins cannot be
  unloaded. At most, a "Restart now" button could be offered in the warning.
