#!/usr/bin/env python3
"""
Advanced Features Demonstration

This script demonstrates all the advanced features implemented in the
Ultimate Flashcard Generation System including:
- Progressive disclosure cards
- Interactive code execution cards
- Visual diagram completion cards
- Multi-modal content processing
- Advanced analytics dashboard
- Enhanced CLI interface
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Import our advanced modules
try:
    from advanced_features import (
        create_progressive_card,
        create_interactive_code_card,
        create_diagram_card,
        AdvancedTemplateSelector
    )
    from analytics_dashboard import create_analytics_dashboard
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    HAS_ADVANCED_FEATURES = True
except ImportError as e:
    print(f"Advanced features not available: {e}")
    HAS_ADVANCED_FEATURES = False

console = Console() if HAS_ADVANCED_FEATURES else None


def demo_progressive_disclosure_cards():
    """Demonstrate progressive disclosure cards"""
    if not console:
        print("Rich console not available")
        return
    
    console.print("\n[bold blue]Progressive Disclosure Cards Demo[/bold blue]\n")
    
    # Example: Machine Learning concept
    concept = "Machine Learning"
    levels = [
        "A subset of AI that learns from data",
        "Uses algorithms to find patterns in data without explicit programming",
        "Includes supervised, unsupervised, and reinforcement learning approaches",
        "Applications include image recognition, natural language processing, and recommendation systems"
    ]
    
    card = create_progressive_card(concept, levels, context="Computer Science Education")
    
    # Display the card structure
    card_table = Table(title="Progressive Disclosure Card Structure")
    card_table.add_column("Level", style="cyan")
    card_table.add_column("Content", style="green")
    card_table.add_column("Complexity", style="yellow")
    
    for level_data in card["levels"]:
        card_table.add_row(
            str(level_data["level"]),
            level_data["content"][:50] + "..." if len(level_data["content"]) > 50 else level_data["content"],
            level_data["complexity"]
        )
    
    console.print(card_table)
    
    # Show JSON structure
    console.print("\n[bold]Card JSON Structure:[/bold]")
    syntax = Syntax(json.dumps(card, indent=2)[:500] + "...", "json", theme="monokai")
    console.print(syntax)
    
    return card


def demo_interactive_code_cards():
    """Demonstrate interactive code execution cards"""
    if not console:
        print("Interactive code cards demo not available")
        return
    
    console.print("\n[bold blue]Interactive Code Execution Cards Demo[/bold blue]\n")
    
    # Example: Fibonacci function
    code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
    
    test_cases = [(0, 0), (1, 1), (5, 5), (10, 55)]
    explanation = "Recursive implementation of the Fibonacci sequence"
    
    card = create_interactive_code_card(code, test_cases, explanation)
    
    # Display card information
    info_table = Table(title="Interactive Code Card")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Language", card["language"])
    info_table.add_row("Test Cases", str(len(card["test_cases"])))
    info_table.add_row("Interactive Elements", str(len(card["interactive_elements"])))
    info_table.add_row("Complexity", str(card["code_analysis"]["complexity"]))
    
    console.print(info_table)
    
    # Show code with syntax highlighting
    console.print("\n[bold]Code Content:[/bold]")
    syntax = Syntax(card["code"], "python", theme="monokai")
    console.print(syntax)
    
    return card


def demo_visual_diagram_cards():
    """Demonstrate visual diagram completion cards"""
    if not console:
        print("Visual diagram cards demo not available")
        return
    
    console.print("\n[bold blue]Visual Diagram Completion Cards Demo[/bold blue]\n")
    
    # Example: Neural network diagram
    missing_components = ["activation_function", "weights", "bias"]
    metadata = {"layers": [3, 4, 2], "type": "feedforward"}
    
    card = create_diagram_card(
        "neural_network", 
        missing_components, 
        description="Complete the neural network architecture",
        metadata=metadata
    )
    
    # Display diagram information
    diagram_table = Table(title="Visual Diagram Card")
    diagram_table.add_column("Property", style="cyan")
    diagram_table.add_column("Value", style="green")
    
    diagram_table.add_row("Diagram Type", card["diagram_type"])
    diagram_table.add_row("Missing Components", str(len(card["missing_components"])))
    diagram_table.add_row("Interactive Elements", str(len(card["interactive_elements"])))
    diagram_table.add_row("Available Components", str(len(card["diagram_data"]["components"])))
    
    console.print(diagram_table)
    
    # Show missing components
    console.print(f"\n[bold]Missing Components:[/bold] {', '.join(missing_components)}")
    console.print(f"[bold]Available Components:[/bold] {', '.join(card['diagram_data']['components'])}")
    
    return card


def demo_template_selector():
    """Demonstrate advanced template selection"""
    if not console:
        print("Template selector demo not available")
        return
    
    console.print("\n[bold blue]Advanced Template Selection Demo[/bold blue]\n")
    
    selector = AdvancedTemplateSelector()
    
    # Show template categories
    categories_table = Table(title="Template Categories")
    categories_table.add_column("Level", style="cyan")
    categories_table.add_column("Options", style="green")
    
    categories_table.add_row("Primary", ", ".join(selector.template_categories["primary"]))
    
    for primary, secondary in selector.template_categories["secondary"].items():
        categories_table.add_row(f"Secondary ({primary})", ", ".join(secondary))
    
    console.print(categories_table)
    
    # Simulate selection
    selection = selector.interactive_selection()
    
    selection_table = Table(title="Template Selection Result")
    selection_table.add_column("Category", style="cyan")
    selection_table.add_column("Selection", style="green")
    
    selection_table.add_row("Primary Type", selection["primary_type"])
    selection_table.add_row("Secondary Types", ", ".join(selection["secondary_types"]))
    selection_table.add_row("Granular Options", ", ".join(selection["granular_options"]))
    
    console.print(selection_table)
    
    return selection


def demo_analytics_dashboard():
    """Demonstrate analytics dashboard"""
    if not console:
        print("Analytics dashboard demo not available")
        return
    
    console.print("\n[bold blue]Analytics Dashboard Demo[/bold blue]\n")
    
    # Create analytics dashboard
    analytics = create_analytics_dashboard("demo_analytics")
    
    # Simulate some study sessions
    sample_sessions = [
        {
            "cards_reviewed": 25,
            "correct_answers": 20,
            "total_time": 15.5,
            "difficulty_level": "intermediate",
            "content_source": "python_tutorial",
            "card_types": ["front_back", "cloze"]
        },
        {
            "cards_reviewed": 30,
            "correct_answers": 24,
            "total_time": 18.2,
            "difficulty_level": "advanced",
            "content_source": "machine_learning",
            "card_types": ["cloze_input", "progressive"]
        },
        {
            "cards_reviewed": 20,
            "correct_answers": 18,
            "total_time": 12.0,
            "difficulty_level": "basic",
            "content_source": "data_structures",
            "card_types": ["front_back", "interactive_code"]
        }
    ]
    
    # Track sessions
    for session in sample_sessions:
        analytics.track_study_session(session)
    
    # Generate analytics
    metrics = analytics.analyze_learning_progress()
    insights = analytics.generate_performance_insights()
    optimization = analytics.optimize_study_schedule()
    
    # Display metrics
    metrics_table = Table(title="Learning Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    
    metrics_table.add_row("Total Cards", str(metrics.total_cards))
    metrics_table.add_row("Cards Mastered", str(metrics.cards_mastered))
    metrics_table.add_row("Average Retention", f"{metrics.average_retention:.2%}")
    metrics_table.add_row("Study Streak", f"{metrics.study_streak} days")
    metrics_table.add_row("Total Study Time", f"{metrics.total_study_time:.1f} minutes")
    
    console.print(metrics_table)
    
    # Display recommendations
    if optimization.get("recommendations"):
        console.print("\n[bold]Study Recommendations:[/bold]")
        for i, rec in enumerate(optimization["recommendations"], 1):
            console.print(f"{i}. [{rec['priority'].upper()}] {rec['suggestion']}")
    
    return analytics


def demo_comprehensive_workflow():
    """Demonstrate a comprehensive workflow using all features"""
    if not console:
        print("Comprehensive workflow demo not available")
        return
    
    console.print("\n[bold green]Comprehensive Workflow Demo[/bold green]\n")
    
    # Step 1: Create different types of cards
    console.print("[bold]Step 1: Creating Advanced Card Types[/bold]")
    
    progressive_card = demo_progressive_disclosure_cards()
    interactive_card = demo_interactive_code_cards()
    diagram_card = demo_visual_diagram_cards()
    
    # Step 2: Template selection
    console.print("\n[bold]Step 2: Advanced Template Selection[/bold]")
    template_selection = demo_template_selector()
    
    # Step 3: Analytics and optimization
    console.print("\n[bold]Step 3: Analytics and Study Optimization[/bold]")
    analytics = demo_analytics_dashboard()
    
    # Step 4: Export comprehensive card set
    console.print("\n[bold]Step 4: Export Comprehensive Card Set[/bold]")
    
    all_cards = [progressive_card, interactive_card, diagram_card]
    
    export_table = Table(title="Export Summary")
    export_table.add_column("Card Type", style="cyan")
    export_table.add_column("Features", style="green")
    export_table.add_column("Educational Value", style="yellow")
    
    export_table.add_row(
        "Progressive Disclosure",
        "Multi-level revelation",
        "Scaffolded learning"
    )
    export_table.add_row(
        "Interactive Code",
        "Real-time execution",
        "Hands-on practice"
    )
    export_table.add_row(
        "Visual Diagram",
        "Interactive completion",
        "Visual understanding"
    )
    
    console.print(export_table)
    
    # Final summary
    console.print("\n[bold green]Workflow Complete![/bold green]")
    console.print("Generated comprehensive flashcard set with:")
    console.print("• Advanced card types for different learning styles")
    console.print("• Intelligent template selection")
    console.print("• Performance analytics and optimization")
    console.print("• Multi-format export capabilities")
    
    return {
        "cards": all_cards,
        "template_selection": template_selection,
        "analytics": analytics
    }


def main():
    """Main demonstration function"""
    if not HAS_ADVANCED_FEATURES:
        print("Advanced features not available. Please install required dependencies.")
        sys.exit(1)
    
    console.print(Panel.fit(
        "[bold blue]Ultimate Flashcard Generation System[/bold blue]\n"
        "[green]Advanced Features Demonstration[/green]",
        border_style="blue"
    ))
    
    try:
        # Run individual demos
        console.print("\n[bold]Running Individual Feature Demos...[/bold]")
        
        demo_progressive_disclosure_cards()
        demo_interactive_code_cards()
        demo_visual_diagram_cards()
        demo_template_selector()
        demo_analytics_dashboard()
        
        # Run comprehensive workflow
        console.print("\n" + "="*60)
        result = demo_comprehensive_workflow()
        
        console.print(f"\n[bold green]Demo completed successfully![/bold green]")
        console.print(f"Generated {len(result['cards'])} advanced cards with full analytics.")
        
    except Exception as e:
        console.print(f"[bold red]Demo failed: {e}[/bold red]")
        if "--verbose" in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
