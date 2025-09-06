#!/usr/bin/env python3
"""
Enhanced CLI for Ultimate Flashcard Generation System

This module provides a rich, interactive command-line interface using:
- Click framework for robust command structure
- Rich library for beautiful terminal output
- Colorama for cross-platform color support
- Interactive prompts and validation
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for cross-platform support
colorama.init()

# Initialize rich console
console = Console()

# Version information
__version__ = "2.0.0"
__author__ = "Ultimate Flashcard Generation System"


class CLIConfig:
    """Configuration management for CLI"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".flashcard_system"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return self.get_default_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            console.print(f"[red]Failed to save config: {e}[/red]")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "gemini_api_key": "",
            "default_output_dir": "exports",
            "default_formats": ["json", "csv"],
            "default_batch_size": 1000,
            "default_memory_threshold": 1000,
            "cache_enabled": True,
            "verbose": False
        }
    
    def update_config(self, key: str, value: Any):
        """Update configuration value"""
        self.config[key] = value
        self.save_config()


# Global config instance
cli_config = CLIConfig()


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Ultimate Flashcard Generation System                      ║
║                           Version 2.0.0 Enhanced                            ║
║                                                                              ║
║  AI-Powered • Multi-Format • Comprehensive • Production-Ready               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_success(message: str):
    """Print success message"""
    console.print(f"✅ {message}", style="bold green")


def print_error(message: str):
    """Print error message"""
    console.print(f"❌ {message}", style="bold red")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"⚠️  {message}", style="bold yellow")


def print_info(message: str):
    """Print info message"""
    console.print(f"ℹ️  {message}", style="bold blue")


def create_progress_bar(description: str = "Processing"):
    """Create a rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def validate_source_url(ctx, param, value):
    """Validate source URL or file path"""
    if not value:
        return value
    
    if value.startswith(('http://', 'https://')):
        return value
    
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"File or URL does not exist: {value}")
    
    return str(path.absolute())


def validate_formats(ctx, param, value):
    """Validate export formats"""
    if not value:
        return ["json", "csv"]
    
    valid_formats = {"json", "csv", "anki", "xlsx", "markdown"}
    formats = [f.strip().lower() for f in value.split(",")]
    
    invalid_formats = set(formats) - valid_formats
    if invalid_formats:
        raise click.BadParameter(f"Invalid formats: {', '.join(invalid_formats)}. Valid: {', '.join(valid_formats)}")
    
    return formats


def interactive_setup():
    """Interactive setup for first-time users"""
    console.print("\n[bold blue]Welcome to the Ultimate Flashcard Generation System![/bold blue]")
    console.print("Let's set up your configuration...\n")
    
    # Gemini API Key
    if not cli_config.config.get("gemini_api_key"):
        gemini_key = Prompt.ask(
            "Enter your Gemini API key (optional, press Enter to skip)",
            password=True,
            default=""
        )
        if gemini_key:
            cli_config.update_config("gemini_api_key", gemini_key)
            print_success("Gemini API key saved")
    
    # Default output directory
    output_dir = Prompt.ask(
        "Default output directory",
        default=cli_config.config.get("default_output_dir", "exports")
    )
    cli_config.update_config("default_output_dir", output_dir)
    
    # Default formats
    formats = Prompt.ask(
        "Default export formats (comma-separated)",
        default=",".join(cli_config.config.get("default_formats", ["json", "csv"]))
    )
    cli_config.update_config("default_formats", formats.split(","))
    
    print_success("Configuration saved!")


def show_system_info():
    """Show system information and status"""
    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Check dependencies
    try:
        import torch
        table.add_row("PyTorch", "✅ Available", f"Version: {torch.__version__}")
    except ImportError:
        table.add_row("PyTorch", "❌ Missing", "Required for AI features")
    
    try:
        import google.generativeai
        table.add_row("Gemini AI", "✅ Available", "Ready for enhanced processing")
    except ImportError:
        table.add_row("Gemini AI", "❌ Missing", "Install google-generativeai")
    
    try:
        from sentence_transformers import SentenceTransformer
        table.add_row("Sentence Transformers", "✅ Available", "AI content analysis ready")
    except ImportError:
        table.add_row("Sentence Transformers", "❌ Missing", "Install sentence-transformers")
    
    # Configuration status
    config_status = "✅ Configured" if cli_config.config.get("gemini_api_key") else "⚠️ Partial"
    table.add_row("Configuration", config_status, f"Config file: {cli_config.config_file}")
    
    console.print(table)


# Main CLI group
@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--setup', is_flag=True, help='Run interactive setup')
@click.option('--info', is_flag=True, help='Show system information')
@click.pass_context
def cli(ctx, version, setup, info):
    """
    Ultimate Flashcard Generation System - Enhanced CLI
    
    A comprehensive AI-powered system for generating educational flashcards
    from various content sources including PDFs, GitHub repositories, 
    HTML documentation, and more.
    """
    if ctx.invoked_subcommand is None:
        if version:
            console.print(f"Ultimate Flashcard Generation System v{__version__}")
            return
        
        if setup:
            interactive_setup()
            return
        
        if info:
            show_system_info()
            return
        
        print_banner()
        console.print("\nUse --help to see available commands or --setup for first-time configuration.\n")


# PDF Processing Command
@cli.command()
@click.argument('input_file', type=click.Path(exists=True), callback=validate_source_url)
@click.option('-o', '--output', default=None, help='Output base name')
@click.option('--formats', default=None, callback=validate_formats, 
              help='Export formats (json,csv,anki,xlsx,markdown)')
@click.option('--comprehensive', is_flag=True, help='Enable comprehensive processing')
@click.option('--use-gemini', is_flag=True, help='Use Gemini AI for enhanced processing')
@click.option('--max-cards', default=100, help='Maximum cards per section')
@click.option('--batch-size', default=None, help='Batch size for large documents')
@click.option('--custom-instructions', help='Custom instructions for card generation')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def pdf(input_file, output, formats, comprehensive, use_gemini, max_cards, 
        batch_size, custom_instructions, verbose):
    """Process PDF documents into flashcards"""
    
    print_banner()
    console.print(f"\n[bold]Processing PDF: {input_file}[/bold]\n")
    
    # Use config defaults if not specified
    if not output:
        output = Path(input_file).stem
    if not formats:
        formats = cli_config.config.get("default_formats", ["json", "csv"])
    if not batch_size:
        batch_size = cli_config.config.get("default_batch_size", 1000)
    
    # Show processing configuration
    config_table = Table(title="Processing Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Input File", input_file)
    config_table.add_row("Output Base", output)
    config_table.add_row("Export Formats", ", ".join(formats))
    config_table.add_row("Comprehensive Mode", "Yes" if comprehensive else "No")
    config_table.add_row("Gemini AI", "Yes" if use_gemini else "No")
    config_table.add_row("Max Cards/Section", str(max_cards))
    config_table.add_row("Batch Size", str(batch_size))
    
    console.print(config_table)
    console.print()
    
    # Confirm processing
    if not Confirm.ask("Proceed with processing?"):
        print_info("Processing cancelled")
        return
    
    # Process with progress bar
    with create_progress_bar("Processing PDF") as progress:
        task = progress.add_task("Extracting content...", total=100)
        
        try:
            # Import and run processing
            from flashcardify_ultimate import UltimateFlashcardSystem
            
            config = {
                'use_ai': True,
                'use_gemini': use_gemini and cli_config.config.get("gemini_api_key"),
                'gemini_api_key': cli_config.config.get("gemini_api_key"),
                'max_cards_per_section': max_cards,
                'batch_size': batch_size,
                'comprehensive': comprehensive,
                'custom_instructions': custom_instructions or '',
                'output_dir': cli_config.config.get("default_output_dir", "exports")
            }
            
            progress.update(task, advance=20, description="Initializing system...")
            system = UltimateFlashcardSystem(config)
            
            progress.update(task, advance=30, description="Processing content...")
            result = system.process_content_comprehensive(input_file, 'pdf')
            
            progress.update(task, advance=30, description="Exporting cards...")
            export_results = system.export_cards(result['cards'], output, formats)
            
            progress.update(task, advance=20, description="Complete!")
            
            # Show results
            console.print("\n[bold green]Processing Complete![/bold green]\n")
            
            results_table = Table(title="Results Summary")
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="green")
            
            results_table.add_row("Total Cards Generated", str(result['total_cards']))
            results_table.add_row("Comprehensive Mode", "Yes" if comprehensive else "No")
            results_table.add_row("AI Enhancement", "Yes" if use_gemini else "No")
            
            console.print(results_table)
            
            # Show export files
            if export_results:
                console.print("\n[bold]Exported Files:[/bold]")
                for format_type, file_path in export_results.items():
                    if file_path:
                        console.print(f"  {format_type.upper()}: {file_path}")
            
            print_success("PDF processing completed successfully!")
            
        except Exception as e:
            progress.update(task, description="Failed!")
            print_error(f"Processing failed: {e}")
            if verbose:
                console.print_exception()


# GitHub Processing Command
@cli.command()
@click.argument('repository_url', callback=validate_source_url)
@click.option('-o', '--output', default=None, help='Output base name')
@click.option('--formats', default=None, callback=validate_formats,
              help='Export formats (json,csv,anki,xlsx,markdown)')
@click.option('--comprehensive', is_flag=True, help='Enable comprehensive processing')
@click.option('--use-gemini', is_flag=True, help='Use Gemini AI for enhanced processing')
@click.option('--max-files', default=20, help='Maximum files to process')
@click.option('--file-types', default='py,js,ts,java,cpp,c,h', 
              help='File extensions to process (comma-separated)')
@click.option('--include-docs', is_flag=True, help='Include documentation files')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def github(repository_url, output, formats, comprehensive, use_gemini, 
           max_files, file_types, include_docs, verbose):
    """Process GitHub repositories into flashcards"""
    
    print_banner()
    console.print(f"\n[bold]Processing GitHub Repository: {repository_url}[/bold]\n")
    
    # Extract repo name for default output
    if not output:
        output = repository_url.split('/')[-1].replace('.git', '')
    if not formats:
        formats = cli_config.config.get("default_formats", ["json", "csv"])
    
    # Show processing configuration
    config_table = Table(title="GitHub Processing Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Repository URL", repository_url)
    config_table.add_row("Output Base", output)
    config_table.add_row("Export Formats", ", ".join(formats))
    config_table.add_row("Max Files", str(max_files))
    config_table.add_row("File Types", file_types)
    config_table.add_row("Include Docs", "Yes" if include_docs else "No")
    config_table.add_row("Comprehensive", "Yes" if comprehensive else "No")
    
    console.print(config_table)
    console.print()
    
    if not Confirm.ask("Proceed with GitHub processing?"):
        print_info("Processing cancelled")
        return
    
    # Process with progress
    with create_progress_bar("Processing GitHub Repository") as progress:
        task = progress.add_task("Accessing repository...", total=100)
        
        try:
            from flashcardify_ultimate import UltimateFlashcardSystem
            
            config = {
                'use_ai': True,
                'use_gemini': use_gemini and cli_config.config.get("gemini_api_key"),
                'gemini_api_key': cli_config.config.get("gemini_api_key"),
                'comprehensive': comprehensive,
                'output_dir': cli_config.config.get("default_output_dir", "exports")
            }
            
            progress.update(task, advance=20, description="Initializing system...")
            system = UltimateFlashcardSystem(config)
            
            progress.update(task, advance=40, description="Processing repository...")
            result = system.process_content_comprehensive(repository_url, 'github')
            
            progress.update(task, advance=30, description="Exporting cards...")
            export_results = system.export_cards(result['cards'], output, formats)
            
            progress.update(task, advance=10, description="Complete!")
            
            # Show results
            console.print("\n[bold green]GitHub Processing Complete![/bold green]\n")
            
            results_table = Table(title="Results Summary")
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="green")
            
            results_table.add_row("Total Cards Generated", str(result['total_cards']))
            results_table.add_row("Repository", repository_url)
            results_table.add_row("Processing Mode", "Comprehensive" if comprehensive else "Standard")
            
            console.print(results_table)
            
            print_success("GitHub repository processing completed successfully!")
            
        except Exception as e:
            progress.update(task, description="Failed!")
            print_error(f"GitHub processing failed: {e}")
            if verbose:
                console.print_exception()


# Configuration Commands
@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command()
def show():
    """Show current configuration"""
    console.print("\n[bold]Current Configuration:[/bold]\n")
    
    config_table = Table()
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    for key, value in cli_config.config.items():
        if key == "gemini_api_key" and value:
            value = "*" * 20  # Hide API key
        config_table.add_row(key, str(value))
    
    console.print(config_table)


@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """Set configuration value"""
    try:
        # Handle boolean values
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        # Handle numeric values
        elif value.isdigit():
            value = int(value)
        
        cli_config.update_config(key, value)
        print_success(f"Configuration updated: {key} = {value}")
    except Exception as e:
        print_error(f"Failed to update configuration: {e}")


@config.command()
def reset():
    """Reset configuration to defaults"""
    if Confirm.ask("Reset all configuration to defaults?"):
        cli_config.config = cli_config.get_default_config()
        cli_config.save_config()
        print_success("Configuration reset to defaults")


# HTML Processing Command
@cli.command()
@click.argument('url', callback=validate_source_url)
@click.option('-o', '--output', default=None, help='Output base name')
@click.option('--formats', default=None, callback=validate_formats,
              help='Export formats (json,csv,anki,xlsx,markdown)')
@click.option('--comprehensive', is_flag=True, help='Enable comprehensive processing')
@click.option('--use-gemini', is_flag=True, help='Use Gemini AI for enhanced processing')
@click.option('--max-sections', default=50, help='Maximum sections to process')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def html(url, output, formats, comprehensive, use_gemini, max_sections, verbose):
    """Process HTML documentation into flashcards"""

    print_banner()
    console.print(f"\n[bold]Processing HTML Documentation: {url}[/bold]\n")

    if not output:
        from urllib.parse import urlparse
        output = urlparse(url).netloc.replace('.', '_')
    if not formats:
        formats = cli_config.config.get("default_formats", ["json", "csv"])

    with create_progress_bar("Processing HTML") as progress:
        task = progress.add_task("Fetching content...", total=100)

        try:
            from flashcardify_ultimate import UltimateFlashcardSystem

            config = {
                'use_ai': True,
                'use_gemini': use_gemini and cli_config.config.get("gemini_api_key"),
                'gemini_api_key': cli_config.config.get("gemini_api_key"),
                'comprehensive': comprehensive,
                'output_dir': cli_config.config.get("default_output_dir", "exports")
            }

            progress.update(task, advance=30, description="Processing content...")
            system = UltimateFlashcardSystem(config)
            result = system.process_content_comprehensive(url, 'html')

            progress.update(task, advance=50, description="Exporting cards...")
            export_results = system.export_cards(result['cards'], output, formats)

            progress.update(task, advance=20, description="Complete!")

            print_success("HTML processing completed successfully!")

        except Exception as e:
            print_error(f"HTML processing failed: {e}")
            if verbose:
                console.print_exception()


# Analytics and Statistics Command
@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--format', 'input_format', default='json',
              type=click.Choice(['json', 'csv']), help='Input file format')
@click.option('--export', is_flag=True, help='Export analytics report')
def analyze(input_path, input_format, export):
    """Analyze generated flashcards and show statistics"""

    console.print(f"\n[bold]Analyzing Flashcards: {input_path}[/bold]\n")

    try:
        if input_format == 'json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cards = data.get('cards', []) if isinstance(data, dict) else data
        else:
            import pandas as pd
            df = pd.read_csv(input_path)
            cards = df.to_dict('records')

        # Generate analytics
        total_cards = len(cards)
        card_types = {}
        difficulties = {}
        tags = set()

        for card in cards:
            card_type = card.get('type', 'unknown')
            card_types[card_type] = card_types.get(card_type, 0) + 1

            difficulty = card.get('difficulty', 'unknown')
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1

            card_tags = card.get('tags', '').split(',')
            tags.update(tag.strip() for tag in card_tags if tag.strip())

        # Display analytics
        analytics_table = Table(title="Flashcard Analytics")
        analytics_table.add_column("Metric", style="cyan")
        analytics_table.add_column("Value", style="green")

        analytics_table.add_row("Total Cards", str(total_cards))
        analytics_table.add_row("Unique Tags", str(len(tags)))
        analytics_table.add_row("Card Types", str(len(card_types)))
        analytics_table.add_row("Difficulty Levels", str(len(difficulties)))

        console.print(analytics_table)

        # Card type distribution
        type_table = Table(title="Card Type Distribution")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green")
        type_table.add_column("Percentage", style="yellow")

        for card_type, count in sorted(card_types.items()):
            percentage = (count / total_cards) * 100
            type_table.add_row(card_type, str(count), f"{percentage:.1f}%")

        console.print(type_table)

        print_success("Analysis completed!")

    except Exception as e:
        print_error(f"Analysis failed: {e}")


# Template Management Commands
@cli.group()
def templates():
    """Template management commands"""
    pass


@templates.command()
def list():
    """List available templates"""
    console.print("\n[bold]Available Templates:[/bold]\n")

    try:
        template_dir = Path("templates")
        if not template_dir.exists():
            print_warning("Templates directory not found")
            return

        template_files = list(template_dir.glob("*.json"))

        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    for category, templates in data.items():
                        if isinstance(templates, list):
                            console.print(f"[cyan]{category}[/cyan]: {len(templates)} templates")
                elif isinstance(data, list):
                    console.print(f"[cyan]{template_file.stem}[/cyan]: {len(data)} templates")

            except Exception as e:
                print_warning(f"Could not read {template_file}: {e}")

    except Exception as e:
        print_error(f"Failed to list templates: {e}")


if __name__ == '__main__':
    cli()
