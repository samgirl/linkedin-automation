"""Test script to verify installation."""

import sys
from pathlib import Path

# Add parent of project root to path so `pros` package is found
project_root = Path(__file__).parent
parent_dir = project_root.parent
sys.path.insert(0, str(parent_dir))


def test_imports():
    """Test all module imports."""
    errors = []
    
    # Core modules
    try:
        from pros.src.db.models import Event, Memory, IdentityNode, Opportunity
        print("✓ Database models")
    except Exception as e:
        errors.append(f"Database models: {e}")
    
    try:
        from pros.src.core.events.service import EventsService
        print("✓ Events service")
    except Exception as e:
        errors.append(f"Events service: {e}")
    
    try:
        from pros.src.core.memory.service import MemoryService
        print("✓ Memory service")
    except Exception as e:
        errors.append(f"Memory service: {e}")
    
    try:
        from pros.src.core.identity.service import IdentityService
        print("✓ Identity service")
    except Exception as e:
        errors.append(f"Identity service: {e}")
    
    try:
        from pros.src.core.reflection.service import ReflectionService
        print("✓ Reflection service")
    except Exception as e:
        errors.append(f"Reflection service: {e}")
    
    # AI modules
    try:
        from pros.src.ai.orchestrator import get_ai
        print("✓ AI orchestrator")
    except Exception as e:
        errors.append(f"AI orchestrator: {e}")
    
    # Opportunity Radar
    try:
        from pros.src.opportunity.radar import OpportunityRadar
        from pros.src.opportunity.scanners import (
            LinkedInScanner, GitHubScanner, RSSScanner, ArxivScanner
        )
        print("✓ Opportunity Radar")
    except Exception as e:
        errors.append(f"Opportunity Radar: {e}")
    
    # Workers
    try:
        from pros.src.workers import (
            EventProcessorWorker, MemoryConsolidatorWorker, OpportunityScannerWorker
        )
        print("✓ Background workers")
    except Exception as e:
        errors.append(f"Background workers: {e}")
    
    # Content generation
    try:
        from pros.src.content.generator import ContentGenerator
        print("✓ Content generator")
    except Exception as e:
        errors.append(f"Content generator: {e}")
    
    # Daily briefing
    try:
        from pros.src.briefing.generator import DailyBriefingGenerator
        print("✓ Daily briefing")
    except Exception as e:
        errors.append(f"Daily briefing: {e}")
    
    # API
    try:
        from pros.src.api.app import create_app
        print("✓ FastAPI app")
    except Exception as e:
        errors.append(f"FastAPI app: {e}")
    
    return errors


def main():
    """Run tests."""
    print("Testing PROS imports...\n")
    
    errors = test_imports()
    
    print()
    if errors:
        print(f"FAIL: {len(errors)} errors found:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("OK: All imports successful!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
