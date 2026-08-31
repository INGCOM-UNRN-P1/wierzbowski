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


def generar_seccion_markdown(report: DependencyAuditReport) -> str:
    """Genera sección de auditoría de inclusión de cabeceras y Makefile para Dredd."""
    lines = ["## Dependencias de Cabeceras y Makefile (Wierzbowski)\n"]
    lines.append(f"- **Cabeceras escaneadas:** {report.total_headers_scanned}")
    lines.append(f"- **Archivos C escaneados:** {report.total_c_files_scanned}")
    lines.append(f"- **Ciclos de inclusión detectados:** {len(report.cycles)}")
    lines.append(f"- **Problemas en guardas de inclusión:** {len(report.guard_issues)}")
    lines.append(f"- **Observaciones de Makefile:** {len(report.makefile_issues)}\n")
    if report.passed:
        lines.append("> [!TIP]\n> **Grafo Modular Limpio:** No se detectaron ciclos de inclusión circular, las guardas son canónicas y el Makefile respeta los estándares.\n")
    else:
        lines.append("> [!WARNING]\n> **Conflictos de Dependencias / Makefile:**\n")
        if report.cycles:
            lines.append("### Inclusiones Circulares")
            for c in report.cycles:
                lines.append(f"- ❌ `{c.description}`")
            lines.append("")
        if report.guard_issues:
            lines.append("### Guardas de Inclusión Problemáticas")
            for g in report.guard_issues:
                lines.append(f"- ⚠️ {g}")
            lines.append("")
        if report.makefile_issues:
            lines.append("### Observaciones en Makefile")
            lines.append("| Código | Severidad | Línea | Diagnóstico | Sugerencia |")
            lines.append("| :---: | :---: | :---: | :--- | :--- |")
            for m in report.makefile_issues:
                lines.append(f"| `{m.code}` | **{m.severity}** | {m.line_number} | {m.message} | {m.suggestion} |")
            lines.append("")
    return "\n".join(lines)


@app.command("audit")
@app.command("check")
def audit(
    directory: Path = typer.Argument(Path("."), help="Directorio raíz del proyecto C a analizar"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
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

    if output_md:
        md_text = generar_seccion_markdown(report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Sección Markdown generada en:[/bold green] {output_md}")
        raise typer.Exit(code=0 if report.passed else 1)

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


@app.command("report")
def report_cmd(
    directory: Path = typer.Argument(Path("."), help="Directorio raíz del proyecto C a analizar"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
):
    """Genera directamente la sección de reporte Markdown de WIERZBOWSKI para Dredd."""
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
    md_content = generar_seccion_markdown(report)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)


@app.command()
def version():
    """Muestra la versión de WIERZBOWSKI."""
    from wierzbowski import __version__
    console.print(f"[bold cyan]WIERZBOWSKI[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
