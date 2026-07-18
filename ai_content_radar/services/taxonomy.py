"""Keyword taxonomy loader and management."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ai_content_radar.config.settings import DATA_DIR

logger = logging.getLogger(__name__)

TAXONOMY_FILE = DATA_DIR / "keyword_taxonomy.json"

DEFAULT_TAXONOMY: dict[str, dict[str, Any]] = {
    "Technology Transfer": {
        "description": "Technology licensing, IP commercialization, knowledge transfer",
        "keywords": [
            {"term": "technology transfer", "weight": 1.2, "aliases": ["tech transfer"], "synonyms": ["innovation transfer"]},
            {"term": "technology licensing", "weight": 1.1, "aliases": ["tech licensing"], "synonyms": []},
            {"term": "ip commercialization", "weight": 1.2, "aliases": ["ip commercialisation"], "synonyms": ["intellectual property commercialization"]},
            {"term": "patent licensing", "weight": 1.1, "aliases": [], "synonyms": ["patent license"]},
            {"term": "patent portfolio", "weight": 0.9, "aliases": [], "synonyms": ["patent estate"]},
            {"term": "innovation transfer", "weight": 1.0, "aliases": [], "synonyms": ["technology transfer"]},
            {"term": "research commercialization", "weight": 1.2, "aliases": ["research commercialisation"], "synonyms": ["research translation"]},
            {"term": "knowledge transfer", "weight": 1.0, "aliases": ["knowledge exchange"], "synonyms": ["knowledge sharing"]},
            {"term": "trl", "weight": 1.0, "aliases": ["technology readiness level"], "synonyms": []},
            {"term": "technology readiness level", "weight": 1.0, "aliases": ["trl"], "synonyms": []},
            {"term": "market readiness level", "weight": 0.9, "aliases": ["mrl"], "synonyms": []},
            {"term": "university spinout", "weight": 1.1, "aliases": ["university spin-off", "academic startup"], "synonyms": ["research spinout"]},
            {"term": "university spin-off", "weight": 1.1, "aliases": ["university spinout"], "synonyms": ["academic startup"]},
            {"term": "academic startup", "weight": 1.0, "aliases": [], "synonyms": ["university spinout"]},
            {"term": "proof of concept", "weight": 1.0, "aliases": ["poc"], "synonyms": ["demonstration"]},
            {"term": "industrial validation", "weight": 0.9, "aliases": [], "synonyms": ["pilot validation"]},
            {"term": "technology scouting", "weight": 1.0, "aliases": [], "synonyms": ["tech scouting"]},
            {"term": "open innovation", "weight": 1.0, "aliases": [], "synonyms": ["collaborative innovation"]},
            {"term": "innovation management", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "innovation diffusion", "weight": 0.8, "aliases": [], "synonyms": ["technology adoption"]},
            {"term": "patent strategy", "weight": 1.0, "aliases": [], "synonyms": ["ip strategy"]},
            {"term": "freedom to operate", "weight": 0.9, "aliases": ["fto"], "synonyms": ["patent clearance"]},
            {"term": "prior art", "weight": 0.8, "aliases": [], "synonyms": []},
            {"term": "patent analytics", "weight": 0.9, "aliases": [], "synonyms": ["patent intelligence"]},
            {"term": "patent landscape", "weight": 0.9, "aliases": [], "synonyms": ["patent map"]},
            {"term": "patent valuation", "weight": 1.0, "aliases": [], "synonyms": ["ip valuation"]},
            {"term": "licensing revenue", "weight": 0.9, "aliases": [], "synonyms": ["royalty income"]},
            {"term": "knowledge exchange", "weight": 0.9, "aliases": [], "synonyms": ["knowledge transfer"]},
            {"term": "research translation", "weight": 1.0, "aliases": [], "synonyms": ["research commercialization"]},
            {"term": "applied research", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "commercial readiness", "weight": 0.9, "aliases": [], "synonyms": ["market readiness"]},
            {"term": "university innovation", "weight": 1.0, "aliases": [], "synonyms": ["academic innovation"]},
            {"term": "research park", "weight": 0.8, "aliases": [], "synonyms": ["science park", "technology park"]},
            {"term": "science park", "weight": 0.8, "aliases": [], "synonyms": ["research park"]},
            {"term": "technology park", "weight": 0.8, "aliases": [], "synonyms": ["research park"]},
            {"term": "startup incubator", "weight": 0.9, "aliases": [], "synonyms": ["incubator"]},
            {"term": "technology incubator", "weight": 0.9, "aliases": [], "synonyms": ["startup incubator"]},
            {"term": "research foundation", "weight": 0.8, "aliases": [], "synonyms": []},
            {"term": "industry academia", "weight": 1.0, "aliases": ["industry-academia"], "synonyms": ["university-industry collaboration"]},
            {"term": "industry collaboration", "weight": 1.0, "aliases": [], "synonyms": ["research collaboration"]},
            {"term": "research collaboration", "weight": 1.0, "aliases": [], "synonyms": ["industry collaboration"]},
            {"term": "university collaboration", "weight": 0.9, "aliases": [], "synonyms": ["academic partnership"]},
        ],
    },
    "Government Innovation": {
        "description": "Government programs, agencies, and innovation policies",
        "keywords": [
            {"term": "dst", "weight": 1.1, "aliases": ["department of science and technology"], "synonyms": []},
            {"term": "dbt", "weight": 1.0, "aliases": ["department of biotechnology"], "synonyms": []},
            {"term": "birac", "weight": 1.1, "aliases": ["biotechnology industry research assistance council"], "synonyms": []},
            {"term": "csir", "weight": 1.1, "aliases": ["council of scientific and industrial research"], "synonyms": []},
            {"term": "icar", "weight": 1.0, "aliases": ["indian council of agricultural research"], "synonyms": []},
            {"term": "iit", "weight": 1.0, "aliases": ["indian institute of technology"], "synonyms": []},
            {"term": "iisc", "weight": 1.0, "aliases": ["indian institute of science"], "synonyms": []},
            {"term": "nrdc", "weight": 0.9, "aliases": ["national research development corporation"], "synonyms": []},
            {"term": "startup india", "weight": 1.1, "aliases": [], "synonyms": []},
            {"term": "msme", "weight": 1.0, "aliases": ["micro small medium enterprises"], "synonyms": ["small business"]},
        ],
    },
    "DeepTech": {
        "description": "Deep tech, advanced manufacturing, robotics, automation",
        "keywords": [
            {"term": "deeptech", "weight": 1.2, "aliases": ["deep tech", "frontier tech"], "synonyms": ["advanced technology"]},
            {"term": "deep tech", "weight": 1.2, "aliases": ["deeptech"], "synonyms": ["frontier tech"]},
            {"term": "frontier tech", "weight": 1.0, "aliases": [], "synonyms": ["deep tech"]},
            {"term": "advanced manufacturing", "weight": 1.1, "aliases": [], "synonyms": ["smart manufacturing"]},
            {"term": "advanced materials", "weight": 1.0, "aliases": [], "synonyms": ["new materials", "material science"]},
            {"term": "robotics", "weight": 1.1, "aliases": ["robot"], "synonyms": ["automation"]},
            {"term": "automation", "weight": 1.0, "aliases": [], "synonyms": ["robotics"]},
            {"term": "industrial ai", "weight": 1.2, "aliases": [], "synonyms": ["ai for manufacturing"]},
            {"term": "computer vision", "weight": 1.0, "aliases": ["cv"], "synonyms": ["visual ai"]},
            {"term": "predictive maintenance", "weight": 1.0, "aliases": ["predmaint"], "synonyms": ["condition monitoring"]},
            {"term": "industrial iot", "weight": 1.1, "aliases": ["iiot"], "synonyms": ["industrial internet of things"]},
            {"term": "digital twin", "weight": 1.1, "aliases": [], "synonyms": ["virtual twin"]},
            {"term": "industry 4.0", "weight": 1.2, "aliases": ["4th industrial revolution"], "synonyms": ["smart industry"]},
            {"term": "factory automation", "weight": 1.0, "aliases": [], "synonyms": ["manufacturing automation"]},
            {"term": "manufacturing excellence", "weight": 0.9, "aliases": [], "synonyms": ["operational excellence"]},
            {"term": "lean manufacturing", "weight": 0.9, "aliases": ["lean production"], "synonyms": []},
            {"term": "six sigma", "weight": 0.8, "aliases": [], "synonyms": []},
            {"term": "quality engineering", "weight": 0.9, "aliases": [], "synonyms": ["quality management"]},
            {"term": "process engineering", "weight": 0.9, "aliases": [], "synonyms": ["chemical engineering"]},
            {"term": "production engineering", "weight": 0.8, "aliases": [], "synonyms": ["manufacturing engineering"]},
            {"term": "supply chain", "weight": 0.9, "aliases": [], "synonyms": ["logistics"]},
        ],
    },
    "Biotechnology": {
        "description": "Synthetic biology, fermentation, bioprocess, enzymes",
        "keywords": [
            {"term": "biotechnology", "weight": 1.2, "aliases": ["biotech"], "synonyms": ["biological technology"]},
            {"term": "synthetic biology", "weight": 1.2, "aliases": ["synbio"], "synonyms": ["synthetic bio"]},
            {"term": "fermentation", "weight": 1.1, "aliases": [], "synonyms": ["industrial fermentation"]},
            {"term": "microbial technology", "weight": 1.0, "aliases": [], "synonyms": ["microbial engineering"]},
            {"term": "industrial microbiology", "weight": 1.0, "aliases": [], "synonyms": ["applied microbiology"]},
            {"term": "metabolic engineering", "weight": 1.1, "aliases": [], "synonyms": ["pathway engineering"]},
            {"term": "precision fermentation", "weight": 1.2, "aliases": [], "synonyms": ["controlled fermentation"]},
            {"term": "bioprocess", "weight": 1.1, "aliases": ["bio-process"], "synonyms": ["bioprocess engineering"]},
            {"term": "bioreactor", "weight": 1.0, "aliases": ["bio-reactor"], "synonyms": ["fermenter"]},
            {"term": "enzymes", "weight": 1.0, "aliases": ["enzyme"], "synonyms": ["biocatalysts"]},
            {"term": "microbial consortia", "weight": 1.0, "aliases": [], "synonyms": ["microbial community"]},
            {"term": "bioeconomy", "weight": 1.1, "aliases": ["bio-economy"], "synonyms": ["biological economy"]},
            {"term": "circular bioeconomy", "weight": 1.1, "aliases": [], "synonyms": ["sustainable bioeconomy"]},
        ],
    },
    "AgTech": {
        "description": "Agriculture technology, precision farming, crop science",
        "keywords": [
            {"term": "agtech", "weight": 1.2, "aliases": ["ag tech", "agri-tech"], "synonyms": ["agriculture technology"]},
            {"term": "precision agriculture", "weight": 1.1, "aliases": ["precision farming"], "synonyms": []},
            {"term": "plant health", "weight": 1.0, "aliases": [], "synonyms": ["crop health"]},
            {"term": "crop nutrition", "weight": 1.0, "aliases": [], "synonyms": ["plant nutrition"]},
            {"term": "soil health", "weight": 1.0, "aliases": [], "synonyms": ["soil quality"]},
            {"term": "soil biology", "weight": 1.0, "aliases": [], "synonyms": ["soil microbiology"]},
            {"term": "rhizosphere", "weight": 0.9, "aliases": [], "synonyms": ["root zone"]},
            {"term": "biostimulants", "weight": 1.1, "aliases": ["bio-stimulants"], "synonyms": []},
            {"term": "biologicals", "weight": 1.0, "aliases": [], "synonyms": ["biological products"]},
            {"term": "biofertilizers", "weight": 1.1, "aliases": ["bio-fertilizers"], "synonyms": []},
            {"term": "biocontrol", "weight": 1.0, "aliases": ["bio-control"], "synonyms": ["biological control"]},
            {"term": "sustainable agriculture", "weight": 1.1, "aliases": [], "synonyms": ["eco-friendly farming"]},
            {"term": "regenerative agriculture", "weight": 1.1, "aliases": [], "synonyms": ["restorative agriculture"]},
            {"term": "digital agriculture", "weight": 1.0, "aliases": [], "synonyms": ["smart farming"]},
            {"term": "drone agriculture", "weight": 1.0, "aliases": [], "synonyms": ["agricultural drones"]},
            {"term": "satellite agriculture", "weight": 0.9, "aliases": [], "synonyms": ["satellite farming"]},
            {"term": "remote sensing", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "climate smart agriculture", "weight": 1.0, "aliases": ["csa"], "synonyms": []},
        ],
    },
    "Tea Industry": {
        "description": "Tea manufacturing, processing, research, exports",
        "keywords": [
            {"term": "tea industry", "weight": 1.2, "aliases": ["tea sector"], "synonyms": []},
            {"term": "tea estate", "weight": 1.1, "aliases": ["tea garden"], "synonyms": []},
            {"term": "tea garden", "weight": 1.1, "aliases": ["tea estate"], "synonyms": []},
            {"term": "tea manufacturing", "weight": 1.1, "aliases": [], "synonyms": ["tea processing"]},
            {"term": "tea processing", "weight": 1.1, "aliases": [], "synonyms": ["tea manufacturing"]},
            {"term": "tea research", "weight": 1.0, "aliases": [], "synonyms": []},
            {"term": "tea innovation", "weight": 1.0, "aliases": [], "synonyms": []},
            {"term": "tea exports", "weight": 0.9, "aliases": ["tea export"], "synonyms": []},
            {"term": "plantation management", "weight": 0.9, "aliases": [], "synonyms": []},
        ],
    },
    "Climate Technology": {
        "description": "Carbon markets, ESG, sustainability, clean tech",
        "keywords": [
            {"term": "climate technology", "weight": 1.2, "aliases": ["climate tech"], "synonyms": ["clean technology"]},
            {"term": "climate tech", "weight": 1.2, "aliases": ["climate technology"], "synonyms": ["clean technology"]},
            {"term": "carbon markets", "weight": 1.1, "aliases": [], "synonyms": ["carbon trading"]},
            {"term": "carbon credits", "weight": 1.1, "aliases": [], "synonyms": ["carbon offset"]},
            {"term": "esg", "weight": 1.1, "aliases": ["environmental social governance"], "synonyms": []},
            {"term": "net zero", "weight": 1.0, "aliases": ["net-zero"], "synonyms": ["carbon neutrality"]},
            {"term": "circular economy", "weight": 1.2, "aliases": [], "synonyms": ["circular business"]},
            {"term": "green manufacturing", "weight": 1.0, "aliases": [], "synonyms": ["sustainable manufacturing"]},
            {"term": "sustainable manufacturing", "weight": 1.0, "aliases": [], "synonyms": ["green manufacturing"]},
            {"term": "clean technology", "weight": 1.0, "aliases": ["cleantech"], "synonyms": ["climate technology"]},
        ],
    },
    "AI and Digital": {
        "description": "AI, LLMs, digital transformation, enterprise software",
        "keywords": [
            {"term": "ai", "weight": 1.1, "aliases": ["artificial intelligence"], "synonyms": ["machine intelligence"]},
            {"term": "generative ai", "weight": 1.2, "aliases": ["genai", "gen ai"], "synonyms": []},
            {"term": "llms", "weight": 1.2, "aliases": ["large language models", "llm"], "synonyms": []},
            {"term": "agentic ai", "weight": 1.2, "aliases": [], "synonyms": ["ai agents"]},
            {"term": "enterprise ai", "weight": 1.1, "aliases": [], "synonyms": ["business ai"]},
            {"term": "knowledge graphs", "weight": 1.0, "aliases": ["knowledge graph"], "synonyms": []},
            {"term": "ai automation", "weight": 1.1, "aliases": [], "synonyms": ["intelligent automation"]},
            {"term": "digital transformation", "weight": 1.2, "aliases": ["digital tranformation", "digi-trans"], "synonyms": ["business digitization"]},
            {"term": "knowledge management", "weight": 1.0, "aliases": ["km"], "synonyms": []},
            {"term": "enterprise software", "weight": 0.9, "aliases": [], "synonyms": ["business software"]},
            {"term": "innovation software", "weight": 0.9, "aliases": [], "synonyms": []},
        ],
    },
    "Manufacturing": {
        "description": "Manufacturing processes, engineering, quality",
        "keywords": [
            {"term": "manufacturing", "weight": 1.1, "aliases": ["mfg"], "synonyms": ["production"]},
            {"term": "smart manufacturing", "weight": 1.1, "aliases": [], "synonyms": ["intelligent manufacturing"]},
            {"term": "additive manufacturing", "weight": 1.0, "aliases": ["3d printing"], "synonyms": []},
            {"term": "manufacturing innovation", "weight": 1.0, "aliases": [], "synonyms": []},
            {"term": "manufacturing process", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "industrial engineering", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "materials science", "weight": 0.9, "aliases": [], "synonyms": ["materials engineering"]},
        ],
    },
    "Startup Ecosystem": {
        "description": "Startups, venture capital, innovation ecosystems",
        "keywords": [
            {"term": "startup ecosystem", "weight": 1.1, "aliases": [], "synonyms": ["startup community"]},
            {"term": "venture capital", "weight": 1.0, "aliases": ["vc"], "synonyms": ["startup funding"]},
            {"term": "seed funding", "weight": 0.9, "aliases": [], "synonyms": ["early stage funding"]},
            {"term": "series a", "weight": 0.8, "aliases": [], "synonyms": []},
            {"term": "startup funding", "weight": 1.0, "aliases": [], "synonyms": ["venture funding"]},
            {"term": "innovation hub", "weight": 0.9, "aliases": [], "synonyms": ["innovation center"]},
            {"term": "entrepreneurship", "weight": 1.0, "aliases": [], "synonyms": ["startup building"]},
            {"term": "deeptech startup", "weight": 1.1, "aliases": [], "synonyms": ["deep tech startup"]},
            {"term": "b2b saas", "weight": 0.8, "aliases": [], "synonyms": ["enterprise saas"]},
        ],
    },
    "University Research": {
        "description": "Academic research, research commercialization",
        "keywords": [
            {"term": "university research", "weight": 1.0, "aliases": ["academic research"], "synonyms": []},
            {"term": "academic research", "weight": 1.0, "aliases": ["university research"], "synonyms": []},
            {"term": "research paper", "weight": 0.8, "aliases": [], "synonyms": ["research publication"]},
            {"term": "research findings", "weight": 0.8, "aliases": [], "synonyms": []},
            {"term": "research breakthrough", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "research innovation", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "lab to market", "weight": 1.1, "aliases": ["lab-to-market"], "synonyms": ["bench to market"]},
            {"term": "research impact", "weight": 0.9, "aliases": [], "synonyms": []},
        ],
    },
    "Industrial Research": {
        "description": "R&D, industrial innovation, applied science",
        "keywords": [
            {"term": "industrial research", "weight": 1.0, "aliases": [], "synonyms": ["corporate research"]},
            {"term": "r&d", "weight": 1.1, "aliases": ["rnd", "research and development"], "synonyms": []},
            {"term": "research and development", "weight": 1.0, "aliases": ["r&d"], "synonyms": []},
            {"term": "corporate r&d", "weight": 0.9, "aliases": [], "synonyms": ["industrial r&d"]},
            {"term": "applied research", "weight": 0.9, "aliases": [], "synonyms": []},
            {"term": "industrial innovation", "weight": 1.0, "aliases": [], "synonyms": []},
            {"term": "research lab", "weight": 0.8, "aliases": ["research laboratory"], "synonyms": []},
            {"term": "technology development", "weight": 0.9, "aliases": [], "synonyms": []},
        ],
    },
}


class KeywordTaxonomy:
    """Manages the keyword taxonomy system."""

    def __init__(self) -> None:
        self.taxonomy_file = TAXONOMY_FILE
        self._taxonomy: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self.taxonomy_file.exists():
            try:
                with open(self.taxonomy_file, "r", encoding="utf-8") as f:
                    self._taxonomy = json.load(f)
                logger.info(f"Loaded taxonomy with {self.total_keywords()} keywords across {len(self._taxonomy)} domains")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load taxonomy: {e}")
                self._taxonomy = DEFAULT_TAXONOMY.copy()
        else:
            self._taxonomy = DEFAULT_TAXONOMY.copy()
            self.save()

    def save(self) -> None:
        self.taxonomy_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.taxonomy_file, "w", encoding="utf-8") as f:
            json.dump(self._taxonomy, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved taxonomy to {self.taxonomy_file}")

    @property
    def domains(self) -> list[str]:
        return list(self._taxonomy.keys())

    def get_domain_keywords(self, domain: str) -> list[dict[str, Any]]:
        return self._taxonomy.get(domain, {}).get("keywords", [])

    def get_all_keywords_flat(self) -> list[dict[str, Any]]:
        result = []
        for domain, data in self._taxonomy.items():
            for kw in data.get("keywords", []):
                result.append({**kw, "domain": domain})
        return result

    def total_keywords(self) -> int:
        return sum(len(data.get("keywords", [])) for data in self._taxonomy.values())

    def add_keyword(
        self,
        domain: str,
        term: str,
        weight: float = 1.0,
        aliases: Optional[list[str]] = None,
        synonyms: Optional[list[str]] = None,
    ) -> None:
        if domain not in self._taxonomy:
            self._taxonomy[domain] = {"description": "", "keywords": []}

        for kw in self._taxonomy[domain]["keywords"]:
            if kw["term"].lower() == term.lower():
                kw["weight"] = weight
                if aliases:
                    kw["aliases"] = aliases
                if synonyms:
                    kw["synonyms"] = synonyms
                self.save()
                return

        self._taxonomy[domain]["keywords"].append({
            "term": term.lower(),
            "weight": weight,
            "aliases": aliases or [],
            "synonyms": synonyms or [],
        })
        self.save()

    def remove_keyword(self, domain: str, term: str) -> bool:
        if domain in self._taxonomy:
            keywords = self._taxonomy[domain]["keywords"]
            original_len = len(keywords)
            self._taxonomy[domain]["keywords"] = [
                kw for kw in keywords if kw["term"].lower() != term.lower()
            ]
            if len(self._taxonomy[domain]["keywords"]) < original_len:
                self.save()
                return True
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for domain, data in self._taxonomy.items():
            for kw in data.get("keywords", []):
                if (
                    query_lower in kw["term"]
                    or any(query_lower in a for a in kw.get("aliases", []))
                    or any(query_lower in s for s in kw.get("synonyms", []))
                ):
                    results.append({**kw, "domain": domain})
        return results

    def get_search_terms(self, domains: Optional[list[str]] = None) -> list[str]:
        terms = []
        target_domains = domains or self.domains
        for domain in target_domains:
            for kw in self.get_domain_keywords(domain):
                terms.append(kw["term"])
                terms.extend(kw.get("aliases", []))
                terms.extend(kw.get("synonyms", []))
        return list(set(terms))
