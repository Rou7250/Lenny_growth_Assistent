import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.database import get_db
from app.models.db_models import Session as SessionModel, Message, Artifact
from app.models.schemas import ChatRequest
from app.providers import get_provider
from app.rag.prompts import build_grounded_prompt, NO_CONTEXT_RESPONSE
from app.rag.retriever import TranscriptRetriever
from app.skills.artifact_generator import extract_artifact, strip_artifact_tags
from app.skills.ship30_writer import build_ship30_prompt

router = APIRouter(prefix="/api/chat", tags=["chat"])
retriever = TranscriptRetriever()


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    session = (
        await db.execute(select(SessionModel).where(SessionModel.id == payload.session_id))
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(session_id=session.id, role="user", content=payload.message, sources=[])
    db.add(user_msg)
    await db.commit()

    chunks = await retriever.retrieve(db, payload.message)
    sources = [
        {
            "episode_title": c.episode_title,
            "guest_name": c.guest_name,
            "timestamp_ref": c.timestamp_ref,
            "similarity": c.similarity,
        }
        for c in chunks
    ]

    async def event_stream():
        if not retriever.has_sufficient_context(chunks):
            yield sse("token", {"text": NO_CONTEXT_RESPONSE})
            assistant_msg = Message(
                session_id=session.id, role="assistant", content=NO_CONTEXT_RESPONSE, sources=[]
            )
            db.add(assistant_msg)
            await db.commit()
            yield sse("done", {"message_id": str(assistant_msg.id), "sources": []})
            return

        context = retriever.build_context(chunks)
        if payload.mode == "ship30":
            system_prompt = build_ship30_prompt(context)
        else:
            system_prompt = build_grounded_prompt(context)

        try:
            provider = get_provider(payload.provider)
        except ValueError as exc:
            yield sse("error", {"detail": str(exc)})
            return

        full_text = ""
        try:
            async for token in provider.generate_response(
                messages=[{"role": "user", "content": payload.message}],
                system_prompt=system_prompt,
            ):
                full_text += token
                yield sse("token", {"text": token})
        except Exception as exc:  # noqa: BLE001
            yield sse("error", {"detail": "The model provider failed to respond. Please try again."})
            return

        artifact_data = extract_artifact(full_text)
        display_text = strip_artifact_tags(full_text) if artifact_data else full_text

        assistant_msg = Message(
            session_id=session.id, role="assistant", content=display_text or full_text, sources=sources
        )
        db.add(assistant_msg)
        await db.flush()

        artifact_id = None
        if artifact_data:
            artifact = Artifact(
                message_id=assistant_msg.id,
                artifact_type=artifact_data["artifact_type"],
                content=artifact_data["content"],
                title=artifact_data["title"],
            )
            db.add(artifact)
            await db.flush()
            artifact_id = str(artifact.id)
            yield sse(
                "artifact",
                {
                    "id": artifact_id,
                    "artifact_type": artifact_data["artifact_type"],
                    "title": artifact_data["title"],
                    "content": artifact_data["content"],
                },
            )

        await db.commit()
        yield sse(
            "done",
            {"message_id": str(assistant_msg.id), "sources": sources, "artifact_id": artifact_id},
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
