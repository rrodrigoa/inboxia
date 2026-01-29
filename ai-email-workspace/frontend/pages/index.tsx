import { useEffect, useState } from 'react';

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

type MailAccount = {
  id: number;
  kind: string;
  imap_host: string;
  imap_user: string;
  smtp_host: string;
  smtp_user: string;
};

type Folder = {
  id: number;
  name: string;
};

type Message = {
  id: number;
  folder_id: number;
  thread_id: number;
  subject: string | null;
  sent_at: string | null;
  from_name: string | null;
  from_email: string | null;
  body_text: string | null;
};

type Thread = {
  id: number;
  subject_norm: string;
  last_date: string | null;
};

type ChatResponse = {
  answer: string;
  citations: { message_id: number; sent_at: string | null; from_email: string | null; subject: string | null }[];
};

export default function Home() {
  const [accounts, setAccounts] = useState<MailAccount[]>([]);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<number | null>(null);
  const [threadMessages, setThreadMessages] = useState<Message[]>([]);
  const [chatQuery, setChatQuery] = useState('');
  const [chatAnswer, setChatAnswer] = useState<ChatResponse | null>(null);
  const [useThread, setUseThread] = useState(false);

  useEffect(() => {
    fetch(`${backendUrl}/api/accounts`)
      .then((res) => res.json())
      .then((data) => {
        setAccounts(data);
        if (data.length > 0) {
          setAccountId(data[0].id);
        }
      });
  }, []);

  useEffect(() => {
    if (!accountId) return;
    fetch(`${backendUrl}/api/folders?account_id=${accountId}`)
      .then((res) => res.json())
      .then((data) => {
        setFolders(data);
        if (data.length > 0) {
          setSelectedFolder(data[0].id);
        }
      });
  }, [accountId]);

  useEffect(() => {
    if (!accountId) return;
    fetch(`${backendUrl}/api/threads?account_id=${accountId}`)
      .then((res) => res.json())
      .then((data) => setThreads(data));
  }, [accountId]);

  useEffect(() => {
    if (!accountId || !selectedFolder) return;
    fetch(`${backendUrl}/api/messages?account_id=${accountId}&folder_id=${selectedFolder}&limit=50`)
      .then((res) => res.json())
      .then((data) => setMessages(data));
  }, [accountId, selectedFolder]);

  useEffect(() => {
    if (!selectedThread) return;
    fetch(`${backendUrl}/api/thread/${selectedThread}`)
      .then((res) => res.json())
      .then((data) => setThreadMessages(data.messages));
  }, [selectedThread]);

  const runChat = async () => {
    if (!accountId || !chatQuery) return;
    const payload = {
      account_id: accountId,
      query: chatQuery,
      selected_thread_id: useThread ? selectedThread : null,
    };
    const res = await fetch(`${backendUrl}/api/chat/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    setChatAnswer(data);
  };

  return (
    <div className="app">
      <aside className="panel">
        <h2>Accounts</h2>
        {accounts.map((account) => (
          <div
            key={account.id}
            className={`list-item ${account.id === accountId ? 'active' : ''}`}
            onClick={() => setAccountId(account.id)}
          >
            {account.imap_user}
          </div>
        ))}
        <h2>Folders</h2>
        {folders.map((folder) => (
          <div
            key={folder.id}
            className={`list-item ${folder.id === selectedFolder ? 'active' : ''}`}
            onClick={() => setSelectedFolder(folder.id)}
          >
            {folder.name}
          </div>
        ))}
      </aside>
      <section className="panel">
        <h2>Inbox</h2>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`list-item ${message.thread_id === selectedThread ? 'active' : ''}`}
            onClick={() => setSelectedThread(message.thread_id)}
          >
            <strong>{message.subject || '(no subject)'}</strong>
            <div>{message.from_email}</div>
          </div>
        ))}
      </section>
      <section className="panel">
        <h2>Thread</h2>
        {threadMessages.map((message) => (
          <div key={message.id} className="list-item">
            <strong>{message.subject || '(no subject)'}</strong>
            <div>{message.from_email}</div>
            <p>{message.body_text}</p>
          </div>
        ))}
      </section>
      <section className="panel chat-panel">
        <h2>AI Chat</h2>
        <div className="chat-box">
          {chatAnswer ? (
            <div>
              <p>{chatAnswer.answer}</p>
              <div>
                {chatAnswer.citations.map((citation) => (
                  <div
                    key={citation.message_id}
                    className="citation"
                    onClick={() => {
                      const match = messages.find((m) => m.id === citation.message_id);
                      if (match) {
                        setSelectedThread(match.thread_id);
                      }
                    }}
                  >
                    Message {citation.message_id}: {citation.subject}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p>Ask a question about your mail.</p>
          )}
        </div>
        <label>
          <input
            type="checkbox"
            checked={useThread}
            onChange={(e) => setUseThread(e.target.checked)}
          />
          Use selected thread as context
        </label>
        <textarea value={chatQuery} onChange={(e) => setChatQuery(e.target.value)} />
        <button onClick={runChat}>Ask</button>
      </section>
    </div>
  );
}
