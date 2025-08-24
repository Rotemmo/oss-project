import typer

app = typer.Typer(add_completion=False, help="LLM-driven C/C++ analyzer")

@app.command()
def analyze(file: str):
    print("No findings.")

if __name__ == "__main__":
    app()
