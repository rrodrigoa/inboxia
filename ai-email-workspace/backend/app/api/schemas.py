from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: int
    email: EmailStr


class MailAccountOut(BaseModel):
    id: int
    kind: str
    imap_host: str
    imap_user: str
    smtp_host: str
    smtp_user: str


class FolderOut(BaseModel):
    id: int
    name: str


class MessageOut(BaseModel):
    id: int
    folder_id: int
    thread_id: int
    subject: Optional[str]
    sent_at: Optional[datetime]
    from_name: Optional[str]
    from_email: Optional[str]
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    body_text: Optional[str]


class ThreadOut(BaseModel):
    id: int
    subject_norm: str
    last_date: Optional[datetime]


class ThreadMessagesOut(BaseModel):
    thread_id: int
    messages: List[MessageOut]


class ChatQueryRequest(BaseModel):
    account_id: int
    query: str
    selected_thread_id: Optional[int] = None


class Citation(BaseModel):
    message_id: int
    sent_at: Optional[datetime]
    from_email: Optional[str]
    subject: Optional[str]


class ChatQueryResponse(BaseModel):
    answer: str
    citations: List[Citation]


class DraftRequest(BaseModel):
    to: List[EmailStr]
    subject_hint: str
    instructions: str


class DraftResponse(BaseModel):
    subject: str
    body: str


class SendRequest(BaseModel):
    account_id: int
    to: List[EmailStr]
    subject: str
    body: str


class SendResponse(BaseModel):
    message_id: int


class IngestRequest(BaseModel):
    account_id: int
