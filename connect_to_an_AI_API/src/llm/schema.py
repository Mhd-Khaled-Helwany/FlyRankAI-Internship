from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

class Category(str, Enum):
    POETRY = "Poetry"
    CHILDRENS_LITERATURE = "Children's literature"
    PICTURE_BOOKS = "Picture books"
    FAIRY_TALES_AND_FOLKLORE = "Fairy tales and folklore"
    FANTASY = "Fantasy"
    SCIENCE_FICTION = "Science fiction"
    GRAPHIC_NOVELS_AND_MANGA = "Graphic novels and manga"
    ROMANCE = "Romance"
    HISTORICAL_FICTION = "Historical fiction"
    MYSTERY = "Mystery"
    PSYCHOLOGICAL_THRILLERS = "Psychological thrillers"
    CRIME = "Crime"
    HORROR = "Horror"
    DYSTOPIAN_FICTION = "Dystopian fiction"
    ADVENTURE_AND_TRAVEL = "Adventure and travel"
    BIOGRAPHY_AND_MEMOIR = "Biography and memoir"
    HISTORY = "History"
    SPORTS = "Sports"
    MUSIC = "Music"
    PHILOSOPHY = "Philosophy"
    POLITICS = "Politics"
    ECONOMICS = "Economics"
    SOCIOLOGY = "Sociology"
    PSYCHOLOGY = "Psychology"
    PERSONAL_DEVELOPMENT = "Personal development"
    SPIRITUALITY_AND_RELIGION = "Spirituality and religion"
    CAREERS = "Careers"
    FOOD = "Food"
    ART = "Art"
    NATURE = "Nature"
    SCIENCE = "Science"
    TECHNOLOGY = "Technology"
    CULTURE = "Culture"
    OTHER = "other"

class QualityFlag(str, Enum):
    ENCODING_ERROR = "encoding_error"
    DUPLICATE_DESCRIPTION = "duplicate_description"
    TRUNCATED_DESCRIPTION = "truncated_description"
    MISSING_DESCRIPTION = "missing_description"
    AMBIGUOUS_CATEGORY = "ambiguous_category"
    NON_ENGLISH_TEXT = "non_english_text"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    LOW_CONFIDENCE = "low_confidence"


class BookRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    title: str = Field(..., min_length=1, max_length=300)
    product_url: HttpUrl
    price_text: str = Field(..., max_length=50)
    price_gbp: float = Field(..., ge=0)
    availability_text: str = Field(..., max_length=200)
    rating_text: str = Field(..., max_length=50)
    description: str = Field(..., max_length=5000)
    source_page: HttpUrl
    fetched_at: datetime

class EnrichRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    record: BookRecord

class EnrichmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    category: Category
    summary: Optional[str] = Field(
        default=None,
        max_length=500,
        description="One sentence. Must be None when the model is unsure "
        "(category='other' case).",
    )
    quality_flags: List[QualityFlag] = Field(default_factory=list)
 