"""
Database Setup Script
"""
#!/usr/bin/env python3

import sys
from pathlib import Path
import click

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.database import init_database, db_manager
from backend.core.config import get_settings

settings = get_settings()


@click.group()
def cli():
    """Database setup and management CLI"""
    pass


@cli.command()
def create_schema():
    """Create database schema"""
    try:
        init_database()
        click.echo("✅ Database schema created successfully")
    except Exception as e:
        click.echo(f"❌ Failed to create schema: {str(e)}")
        sys.exit(1)


@cli.command()
def health_check():
    """Check database health"""
    try:
        healthy = db_manager.health_check()
        if healthy:
            click.echo("✅ Database connection is healthy")
            
            # Show connection info
            conn_info = db_manager.get_connection_info()
            click.echo(f"Connection pool info: {conn_info}")
        else:
            click.echo("❌ Database connection failed")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Database health check failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database? This will delete all data.')
def reset_database():
    """Reset database (CAUTION: destroys all data)"""
    try:
        from backend.core.database import reset_database
        reset_database()
        click.echo("✅ Database reset completed")
    except Exception as e:
        click.echo(f"❌ Database reset failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
