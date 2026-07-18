"""AI router."""

from fastapi import APIRouter
from pydantic import BaseModel

from pros.src.ai.orchestrator import get_ai

router = APIRouter()


class CompleteRequest(BaseModel):
    """Completion request schema."""
    prompt: str
    provider: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000


class CompleteResponse(BaseModel):
    """Completion response schema."""
    text: str
    provider: str


class EmbedRequest(BaseModel):
    """Embedding request schema."""
    text: str


class EmbedResponse(BaseModel):
    """Embedding response schema."""
    embedding: list[float]
    dimensions: int


@router.post("/complete", response_model=CompleteResponse)
async def complete(request: CompleteRequest):
    """Generate a completion."""
    ai = get_ai()
    
    text = await ai.complete(
        request.prompt,
        provider=request.provider,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    return CompleteResponse(
        text=text,
        provider=request.provider or "ollama",
    )


@router.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Generate an embedding."""
    ai = get_ai()
    
    embedding = await ai.embed(request.text)
    
    return EmbedResponse(
        embedding=embedding,
        dimensions=len(embedding),
    )
