from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    DraftRequest,
    DraftResponse,
    FolderOut,
    IngestRequest,
    LoginRequest,
    LoginResponse,
    MailAccountOut,
    MessageOut,
    SendRequest,
    SendResponse,
    ThreadMessagesOut,
    ThreadOut,
)
from app.core.db import get_db
from app.models.models import Folder, MailAccount, Message, Thread
from app.services.auth import authenticate_user
from app.services.chat import answer_question
from app.services.compose import draft_email, send_email
from app.tasks.jobs import ingest_account

router = APIRouter()


@router.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(user_id=user.id, email=user.email)


@router.get("/api/accounts", response_model=list[MailAccountOut])
def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(MailAccount).all()
    return [
        MailAccountOut(
            id=acct.id,
            kind=acct.kind,
            imap_host=acct.imap_host,
            imap_user=acct.imap_user,
            smtp_host=acct.smtp_host,
            smtp_user=acct.smtp_user,
        )
        for acct in accounts
    ]


@router.post("/api/ingest/run")
def run_ingest(payload: IngestRequest):
    ingest_account.delay(payload.account_id)
    return {"status": "queued"}


@router.get("/api/folders", response_model=list[FolderOut])
def list_folders(account_id: int, db: Session = Depends(get_db)):
    folders = db.query(Folder).filter(Folder.account_id == account_id).all()
    return [FolderOut(id=folder.id, name=folder.name) for folder in folders]


@router.get("/api/messages", response_model=list[MessageOut])
def list_messages(
    account_id: int,
    folder_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Message).filter(Message.account_id == account_id)
    if folder_id:
        query = query.filter(Message.folder_id == folder_id)
    messages = query.order_by(Message.sent_at.desc()).limit(limit).offset(offset).all()
    return [
        MessageOut(
            id=message.id,
            folder_id=message.folder_id,
            thread_id=message.thread_id,
            subject=message.subject,
            sent_at=message.sent_at,
            from_name=message.from_name,
            from_email=message.from_email,
            to=message.to_json or [],
            cc=message.cc_json or [],
            bcc=message.bcc_json or [],
            body_text=message.body_text,
        )
        for message in messages
    ]


@router.get("/api/threads", response_model=list[ThreadOut])
def list_threads(account_id: int, folder_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Thread).filter(Thread.account_id == account_id)
    if folder_id:
        message_thread_ids = (
            db.query(Message.thread_id).filter(Message.folder_id == folder_id).distinct().subquery()
        )
        query = query.filter(Thread.id.in_(message_thread_ids))
    threads = query.order_by(Thread.last_date.desc()).all()
    return [
        ThreadOut(id=thread.id, subject_norm=thread.subject_norm, last_date=thread.last_date)
        for thread in threads
    ]


@router.get("/api/thread/{thread_id}", response_model=ThreadMessagesOut)
def get_thread(thread_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.sent_at.asc())
        .all()
    )
    return ThreadMessagesOut(
        thread_id=thread_id,
        messages=[
            MessageOut(
                id=message.id,
                folder_id=message.folder_id,
                thread_id=message.thread_id,
                subject=message.subject,
                sent_at=message.sent_at,
                from_name=message.from_name,
                from_email=message.from_email,
                to=message.to_json or [],
                cc=message.cc_json or [],
                bcc=message.bcc_json or [],
                body_text=message.body_text,
            )
            for message in messages
        ],
    )


@router.post("/api/compose/draft", response_model=DraftResponse)
def compose_draft(payload: DraftRequest):
    subject, body = draft_email(payload.to, payload.subject_hint, payload.instructions)
    return DraftResponse(subject=subject, body=body)


@router.post("/api/compose/send", response_model=SendResponse)
def compose_send(payload: SendRequest, db: Session = Depends(get_db)):
    message = send_email(db, payload.account_id, payload.to, payload.subject, payload.body)
    return SendResponse(message_id=message.id)


@router.post("/api/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest, db: Session = Depends(get_db)):
    answer, citations = answer_question(db, payload.account_id, payload.query, payload.selected_thread_id)
    return ChatQueryResponse(answer=answer, citations=citations)
