#!/usr/bin/env python3
"""
Football Match Prediction Service CLI
"""

import typer
from services.commands import app as ingest_app
from ml.features.build import app as features_app
from ml.training.train import app as train_app
from ml.evaluation.eval import app as eval_app

app = typer.Typer()

# Add subcommands
app.add_typer(ingest_app, name="ingest", help="Data ingestion commands")
app.add_typer(features_app, name="features", help="Feature engineering commands")
app.add_typer(train_app, name="train", help="Model training commands")
app.add_typer(eval_app, name="eval", help="Model evaluation commands")


@app.command()
def serve():
    """Start the FastAPI server"""
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.command()
def setup():
    """Setup the application (database, models, etc.)"""
    typer.echo("Setting up Football Match Prediction Service...")
    
    # Create database tables
    from database.db import engine
    from database.models import Base
    
    typer.echo("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    typer.echo("Database tables created successfully!")
    
    # Create artifacts directory
    import os
    from config import settings
    
    os.makedirs(settings.model_dir, exist_ok=True)
    typer.echo(f"Model directory created: {settings.model_dir}")


if __name__ == "__main__":
    app()
