"""Opportunity scanner worker - scans for opportunities."""

from pros.src.workers.base import BaseWorker
from pros.src.db.database import get_session
from pros.src.opportunity.radar import OpportunityRadar


class OpportunityScannerWorker(BaseWorker):
    """Scans external sources for opportunities."""
    
    def __init__(self):
        super().__init__(interval_minutes=60)  # Run every hour
    
    async def run_once(self):
        """Scan for new opportunities."""
        async for session in get_session():
            try:
                radar = OpportunityRadar(session)
                
                # Scan all sources
                results = await radar.scan(
                    user_id="default_user",  # TODO: Get from config
                    sources=None,  # All sources
                )
                
                if results:
                    # Rank opportunities
                    ranked = await radar.rank("default_user", results)
                    
                    # Save top opportunities
                    await radar.save("default_user", ranked[:20])
                    
                    print(f"Found {len(ranked)} opportunities, saved top 20")
                
            except Exception as e:
                print(f"Opportunity scanning error: {e}")
