"""
API endpoints for dictionary functionality.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Word

router = APIRouter()


@router.get("/{word}")
async def get_word_definition(word: str, db: AsyncSession = Depends(get_db)):
    """
    Get dictionary definition for a Telugu word.
    """
    result = await db.execute(select(Word).where(Word.word == word))
    word_entry = result.scalar_one_or_none()

    if not word_entry:
        raise HTTPException(status_code=404, detail="Word not found in dictionary")

    return {
        "word": word_entry.word,
        "root_form": word_entry.root_form,
        "definitions": word_entry.definitions,
        "part_of_speech": word_entry.part_of_speech,
        "examples": word_entry.examples,
    }
