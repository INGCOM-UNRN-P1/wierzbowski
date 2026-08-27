"""CLI principal de WIERZBOWSKI."""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from wierzbowski.core.models import DependencyAuditReport
from wierzbowski.core.header_graph import build_dependency_graph, detect_cycles
from wierzbowski.core.guard_checker import check_header_guard, lint_makefile

app = typer.Typer(
    name="wierzbowski",
    help="Auditor de grafos de inclusión de headers, dependencias circulares y Makefiles",
    add_completion=True
)
console = Console()


@app.command()
def audit(
    directory: Path = typer.Argument(Path("."), help="Directorio raíz del proyecto C a analizar"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado")
):
    """Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles."""
    nodes = build_dependency_graph(directory)
    cycles = detect_cycles(nodes)

    guard_issues = []
    headers = list(directory.glob("**/*.h"))
    for h in headers:
        ok, msg = check_header_guard(h)
        if not ok:
            guard_issues.append(f"{h.name}: {msg}")

    makefile_path = directory / "Makefile"
    mk_issues = lint_makefile(makefile_path) if makefile_path.exists() else []

    passed = (len(cycles) == 0) and (len(guard_issues) == 0) and not any(i.severity == "ERROR" for i in mk_issues)
    report = DependencyAuditReport(
        total_headers_scanned=len(headers),
        total_c_files_scanned=len(list(directory.glob("**/*.c"))),
        nodes=nodes,
        cycles=cycles,
        guard_issues=guard_issues,
        makefile_issues=mk_issues,
        passed=passed
    )

    if json_output:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        if not report.passed:
            raise typer.Exit(code=1)
        return

    # Renderizado Rich
    tree = Tree("[bold cyan]Grafo de Inclusión del Proyecto[/bold cyan]")
    for name, node in nodes.items():
        sub = tree.add(f"[green]{name}[/green]")
        for inc in node.includes:
            sub.add(f"[dim]➔ {inc}[/dim]")
    console.print(tree)

    if cycles:
        console.print("\n[bold red]🚨 Dependencias Circulares Detectadas:[/bold red]")
        for c in cycles:
            console.print(f"  [red]• Ciclo: {c.description}[/red]")

    if guard_issues:
        console.print("\n[bold yellow]⚠️ Problemas en Guardas de Inclusión:[/bold yellow]")
        for g in guard_issues:
            console.print(f"  [yellow]• {g}[/yellow]")

    if mk_issues:
        table = Table(title="Auditoría de Makefile", show_header=True, header_style="bold blue")
        table.add_column("Código", style="cyan")
        table.add_column("Sev", style="bold")
        table.add_column("Línea", style="dim")
        table.add_column("Mensaje y Sugerencia", style="white")
        for iss in mk_issues:
            sev_color = "red" if iss.severity == "ERROR" else "yellow"
            table.add_row(
                iss.code,
                f"[{sev_color}]{iss.severity}[/{sev_color}]",
                str(iss.line_number),
                f"{iss.message}\n[dim]↳ Sugerencia: {iss.suggestion}[/dim]"
            )
        console.print(table)

    if report.passed:
        console.print("\n[bold green]✓ Grafo de dependencias limpio sin ciclos ni errores de inclusión.[/bold green]")
    else:
        raise typer.Exit(code=1)


@app.command()
def version():
    """Muestra la versión de WIERZBOWSKI."""
    from wierzbowski import __version__
    console.print(f"[bold cyan]WIERZBOWSKI[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
