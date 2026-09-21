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
from wierzbowski.core.guard_checker import auditar_guardas, lint_makefile

app = typer.Typer(
    name="wierzbowski",
    help="Auditor de grafos de inclusión de headers, dependencias circulares y Makefiles",
    add_completion=True
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        from wierzbowski import __version__
        typer.echo(f"wierzbowski {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=_version_callback, is_eager=True,
        help="Muestra la versión de wierzbowski y sale.",
    ),
) -> None:
    """Auditor de grafos de inclusión de headers, dependencias circulares y Makefiles."""


def _auditar_directorio(directory: Path) -> DependencyAuditReport:
    """Recolecta grafo, ciclos, guardas y Makefile; lo comparten `audit` y `report`."""
    nodes = build_dependency_graph(directory)
    cycles = detect_cycles(nodes)
    headers = sorted(directory.glob("**/*.h"))
    guard_issues, guard_notes = auditar_guardas(headers)
    makefile_path = directory / "Makefile"
    mk_issues = lint_makefile(makefile_path) if makefile_path.exists() else []
    passed = (len(cycles) == 0) and (len(guard_issues) == 0) and not any(i.severity == "ERROR" for i in mk_issues)
    return DependencyAuditReport(
        total_headers_scanned=len(headers),
        total_c_files_scanned=len(list(directory.glob("**/*.c"))),
        nodes=nodes,
        cycles=cycles,
        guard_issues=guard_issues,
        guard_notes=guard_notes,
        makefile_issues=mk_issues,
        passed=passed,
    )


def generar_seccion_markdown(report: DependencyAuditReport) -> str:
    """Genera sección de auditoría de inclusión de cabeceras y Makefile para Dredd."""
    lines = [
        "<!-- dredd-section: wierzbowski v1.0.0 -->\n",
        "## Dependencias de Cabeceras y Makefile (Wierzbowski)\n",
    ]
    lines.append(f"- **Cabeceras escaneadas:** {report.total_headers_scanned}")
    lines.append(f"- **Archivos C escaneados:** {report.total_c_files_scanned}")
    lines.append(f"- **Ciclos de inclusión detectados:** {len(report.cycles)}")
    lines.append(f"- **Problemas en guardas de inclusión:** {len(report.guard_issues)}")
    lines.append(f"- **Avisos en guardas de inclusión:** {len(report.guard_notes)}")
    lines.append(f"- **Observaciones de Makefile:** {len(report.makefile_issues)}\n")
    if report.guard_notes:
        lines.append("> [!NOTE]\n> **Guardas que no corresponden al archivo:**")
        for n in report.guard_notes:
            lines.append(f"> - {n}")
        lines.append("")
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
                msg_limpio = m.message.replace("|", "&#124;")
                sug_limpio = m.suggestion.replace("|", "&#124;")
                lines.append(f"| `{m.code}` | **{m.severity}** | {m.line_number} | {msg_limpio} | {sug_limpio} |")
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
    report = _auditar_directorio(directory)
    nodes, cycles = report.nodes, report.cycles
    guard_issues, guard_notes = report.guard_issues, report.guard_notes
    mk_issues = report.makefile_issues

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

    if guard_notes:
        console.print("\n[bold cyan]ℹ Avisos en Guardas de Inclusión:[/bold cyan]")
        for n in guard_notes:
            console.print(f"  [cyan]• {n}[/cyan]")

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
    report = _auditar_directorio(directory)
    md_content = generar_seccion_markdown(report)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)


@app.command("doctor")
def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir diagnóstico en formato JSON estructurado."),
) -> None:
    """Verifica el estado del entorno de auditoría de dependencias WIERZBOWSKI (Python, Make, GCC)."""
    import shutil
    import sys
    diagnostico = []

    py_ok = sys.version_info >= (3, 10)
    diagnostico.append({
        "componente": "Python Runtime",
        "estado": "OK" if py_ok else "ERROR",
        "requerido": True,
        "detalle": f"Python {sys.version.split()[0]}",
    })

    make_path = shutil.which("make")
    diagnostico.append({
        "componente": "GNU Make",
        "estado": "OK" if make_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": make_path or "No encontrado (opcional para validación de Makefiles)",
    })

    gcc_path = shutil.which("gcc")
    diagnostico.append({
        "componente": "Compilador GCC",
        "estado": "OK" if gcc_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": gcc_path or "No encontrado (opcional para preprocesamiento de inclusión)",
    })

    todo_ok = py_ok

    if json_output:
        payload = {
            "schema_version": "1.0.0",
            "herramienta": "wierzbowski",
            "ok": todo_ok,
            "componentes": diagnostico,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if todo_ok else 1)

    tabla = Table(title="🏥 Diagnóstico del Entorno WIERZBOWSKI (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle")

    for c in diagnostico:
        color = "bold green" if c["estado"] == "OK" else ("bold yellow" if c["estado"] == "ADVERTENCIA" else "bold red")
        simbolo = "✓" if c["estado"] == "OK" else ("⚠️" if c["estado"] == "ADVERTENCIA" else "✗")
        tabla.add_row(c["componente"], f"[{color}]{simbolo} {c['estado']}[/{color}]", c["detalle"])

    console.print(tabla)
    if not todo_ok:
        raise typer.Exit(code=1)


@app.command(hidden=True)
def version():
    """Muestra la versión de WIERZBOWSKI."""
    from wierzbowski import __version__
    console.print(f"[bold cyan]WIERZBOWSKI[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
