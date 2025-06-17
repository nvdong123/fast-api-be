# app/cli.py
import typer
from app.scripts.seed_data import main as seed_main

app = typer.Typer()

@app.command()
def seed():
    """
    Seed demo data into the database
    """
    try:
        seed_main()
        typer.echo("Data seeding completed successfully!")
    except Exception as e:
        typer.echo(f"Error seeding data: {str(e)}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()