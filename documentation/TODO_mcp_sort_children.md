TODO: `sort_children` tool in the PROTEUS MCP server
====================================================

## Problem

The GUI lets the user sort the children of a section (or document) alphabetically from the
context menu. The MCP server (`resources/plugins/proteus_mcp`) has no equivalent tool, so
an MCP client can only emulate it by reading the children and calling `move_artifact`
once per misplaced object (many calls, and a sort criterion that may differ from the
GUI's).

## Proposal

Add a tool to `resources/plugins/proteus_mcp/tools.py`:

```python
@mcp.tool()
def sort_children(object_id: str, reverse: bool = False) -> str:
    """Sort the children of an artifact alphabetically by name (or code + name)."""
```

and a method in `resources/plugins/proteus_mcp/gateway.py` next to `move_object`:

```python
def sort_children(self, object_id: ProteusID, reverse: bool = False) -> None:
    self._controller.sort_object_children(object_id, reverse)
```

`ProjectController.sort_object_children` (`proteus/controller/command_stack.py`) already
pushes a `SortChildrenCommand` (undoable, notifies the GUI with `SortChildrenEvent`), which
calls `ProjectService.sort_children_by_name`. Reusing it gives the same criterion as the
menu entry, and keeps the GUI in sync and the operation in the undo stack.

The tool should return the new children order (`- Name (`id`) [classes]`, as in the
`## Children` list of `get_object`), so the client does not need another call to check it.

## Tasks

- [ ] Add `sort_children` to `gateway.py` and `tools.py` (run it through `_run(bridge, ...)`
      like the other tools, so it executes on the GUI thread).
- [ ] Reject ids that are not objects/documents with children, with a clear error
      (`sort_children_by_name` asserts the element is an `Object`).
- [ ] Return the sorted children list in the result.
- [ ] Document the tool wherever the MCP tools are listed (check `README.md` and the
      plugin docs; `proteus-project-format` skill table if it mentions the tools).
- [ ] Decide and implement locale-aware collation in `sort_children_by_name` (see the
      section below), for the GUI and the MCP tool.
- [ ] Add tests next to the existing plugin tests (`proteus/tests/plugins/`): sorted order,
      `reverse=True`, undo restores the previous order, error for an id that does not exist.

## Sort criterion: use locale-aware collation

`ProjectService.sort_children_by_name` (`proteus/services/project_service.py`) sorts with
a plain string comparison on `"<code> <name>"` or `<name>`, i.e. by Unicode code point.
This is case- and accent-sensitive: lowercase names and names starting with an accented
letter (e.g. "Pádel", "Álbum") sort after the rest ("Pádel" ends up after "Pilates" and
"Pista"), which is wrong for any language that uses diacritics.

Collation is the language-specific rule for ordering text, and it is **not specific to
Spanish**: accents are ignored at the first level in Spanish and French ("Pádel" sorts as
"Padel"), "ñ" is a separate letter between "n" and "o" in Spanish, and in Swedish "å",
"ä" and "ö" come after "z". Therefore the order must depend on a language, not on a
hard-coded rule.

Proposal:

- Sort with a collation key for the **project/profile language** (`es_ES`, `en_US`, ...,
  the language PROTEUS already uses for archetypes and i18n), not the OS locale, so the
  result is the same on every machine.
- Apply it in `sort_children_by_name`, so the GUI context menu and the MCP
  `sort_children` tool share it.
- Implementation options to evaluate:
  - `locale.strxfrm` with `locale.setlocale`: no new dependency, but it depends on the
    locales installed in the OS (Windows names differ from POSIX ones) and it changes
    global process state. Probably not suitable.
  - ICU (`PyICU` or `icu4py`): CLDR rules per language, correct and portable, but adds a
    native dependency to `requirements.txt` and to the PyInstaller build (`Proteus.spec`).
  - Qt: `QCollator` (PyQt6, already a dependency) with `QLocale(<language>)`, set
    `setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)`. Likely the cheapest option;
    check it works without a running `QApplication` (tests) and that
    `QCollator.sortKey` / `compare` behave the same on Windows, Linux and macOS.
  - Fallback without dependencies: `unicodedata.normalize("NFKD", name)` stripping
    combining marks + `str.casefold()`. Good enough for accents and case, but no
    language-specific letters ("ñ" would sort as "n").
- Keep the `:Proteus-code` prefix behaviour (sort by `"<code> <name>"`); with codes, numeric
  order inside the same prefix (`UC-2` before `UC-10`) is a separate question, decide
  whether to enable `QCollator.setNumericMode(True)`.

Tests: update `proteus/tests/end2end/test_sort_children.py` with names that need
collation (e.g. "Pádel", "Pilates", "Pista", "ñu", "Zeta", "abonado") in `es_ES`, and
check that `en_US` and `es_ES` give the expected order for the same input.

## References

- GUI action: `proteus/controller/command_stack.py` (`sort_object_children`),
  `proteus/controller/commands/sort_children.py`, `proteus/application/events.py`
  (`SortChildrenEvent`).
- MCP: `resources/plugins/proteus_mcp/tools.py`, `gateway.py`.
