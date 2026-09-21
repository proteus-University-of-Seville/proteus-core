# ==========================================================================
# File: __main__.py
# Description: entry point for the Proteus application
# Date: 10/09/2026
# Version: 1.1
# Author: Amador Durán Toro
# ==========================================================================

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from proteus import PROTEUS_VERSION, PROTEUS_VERSION_YEAR, parser
from proteus.app import ProteusApplication

# --------------------------------------------------------------------------
# Function: print_banner
# Description: Print the PROTEUS application banner
# Date: 10/09/2026
# Version: 1.0
# Author: Amador Durán Toro
# --------------------------------------------------------------------------

def print_banner() -> None:
    console = Console()
    content = (
        f"[bold cyan]Proteus Application[/bold cyan] [dim]{PROTEUS_VERSION} ({PROTEUS_VERSION_YEAR})[/dim]\n\n"
        f"University of Seville (Andalucía, Spain)\n"
        f"[dim]Distributed under the BSD 3-Clause License[/dim]\n\n"
        f"[bold]Developers:[/bold] José María Delgado Sánchez & other students\n"
        f"[bold]Supervisor:[/bold] Prof. Amador Durán Toro"
    )
    console.print(
        Panel(
            content,
            title="[bold blue]PROTEUS[/bold blue]",
            border_style="cyan",
            expand=False,
        )
    )

# --------------------------------------------------------------------------
# Function: main
# Description: Entry point for the PROTEUS application
# Date: 10/09/2026
# Version: 1.1
# Author: Amador Durán Toro
# --------------------------------------------------------------------------

def main() -> int:
    # Get argument from the command line (if any)
    args = parser.parse_args()

    # The only valid argument is the project path, which is optional.
    # If provided, it must be a valid path.
    project_path: Path = None

    if args.project_path:
        project_path = Path(args.project_path)
        if not project_path.exists():
            print(f"ERROR: The project path '{project_path}' does not exist.")
            return 1

    print_banner()

    app = ProteusApplication(project_path=project_path)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
