# היה:
# file: str = typer.Argument(. help="Path to C/C++ file to analyze"),

# צריך להיות:
file: str = typer.Argument(..., help="Path to C/C++ file to analyze")
