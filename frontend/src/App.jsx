import { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, ArrowUpRight, BookOpen, Check, ChevronRight, CircleHelp, Database, FileText, FlaskConical, LoaderCircle, Menu, Paperclip, PanelLeft, Plus, RefreshCw, Search, Send, Sparkles, Upload, X } from 'lucide-react'
import { createReport, getActivity, getHealth, getSources, queryResearch, uploadSources } from './api'

const navItems = [{ id: 'research', label: 'Research', icon: FlaskConical }, { id: 'sources', label: 'Sources', icon: Database }, { id: 'activity', label: 'Activity', icon: Activity }]

function StatusChip({ mode }) {
  const online = mode === 'anthropic'
  return <span className={`status-chip ${online ? 'status-live' : 'status-local'}`}><span className="status-dot" />{online ? 'Model connected' : 'Offline mode'}</span>
}

function EmptyState({ icon: Icon, title, body, action }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={19} /></div><strong>{title}</strong><p>{body}</p>{action}</div>
}

function Citation({ citation, active, onSelect }) {
  return <button className={`citation ${active ? 'citation-active' : ''}`} onClick={() => onSelect(citation)}><span className="citation-id">{citation.citation_id}</span><span className="citation-body"><strong>{citation.source_name}</strong><span>{citation.excerpt}</span></span><ChevronRight size={15} /></button>
}

function AnswerText({ text }) {
  return <>{text.split(/(\*\*[^*]+\*\*|\[S\d+\])/g).map((part, index) => part.startsWith('**') ? <strong key={index}>{part.slice(2, -2)}</strong> : part.match(/^\[S\d+\]$/) ? <span className="inline-citation" key={index}>{part}</span> : part)}</>
}

function App() {
  const [view, setView] = useState('research')
  const [health, setHealth] = useState({ mode: 'offline', indexed_chunks: 0 })
  const [sources, setSources] = useState([])
  const [activity, setActivity] = useState([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [selectedCitation, setSelectedCitation] = useState(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [mobileNav, setMobileNav] = useState(false)
  const fileInput = useRef(null)

  const refresh = async () => {
    try {
      const [nextHealth, nextSources, nextActivity] = await Promise.all([getHealth(), getSources(), getActivity()])
      setHealth(nextHealth); setSources(nextSources.sources); setActivity(nextActivity.events)
    } catch (err) { setError(err.message) }
  }
  useEffect(() => { refresh() }, [])

  const submitQuestion = async (event) => {
    event?.preventDefault()
    if (!question.trim() || busy) return
    setBusy(true); setError(''); setNotice('')
    try { const result = await queryResearch(question); setAnswer(result); setSelectedCitation(result.citations?.[0] || null); await refresh() }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    setBusy(true); setError(''); setNotice('')
    try { const result = await uploadSources(files); setNotice(`${result.indexed} source${result.indexed === 1 ? '' : 's'} indexed · ${result.total_chunks} passages ready`); await refresh(); setView('sources') }
    catch (err) { setError(err.message) }
    finally { setBusy(false); event.target.value = '' }
  }

  const downloadReport = async () => {
    if (!answer) return
    try { const result = await createReport(answer); const blob = new Blob([result.markdown], { type: 'text/markdown' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = result.filename; link.click(); URL.revokeObjectURL(url); setNotice('Report downloaded') }
    catch (err) { setError(err.message) }
  }

  const selectedText = selectedCitation?.excerpt || 'Select a citation to inspect the exact passage used by the answer.'
  const recentActivity = useMemo(() => activity.slice(0, 8), [activity])

  return <div className="app-shell">
    <aside className={`rail ${mobileNav ? 'rail-open' : ''}`}>
      <div className="rail-brand"><div className="brand-mark">FN</div><span>FIELDNOTES</span><button className="mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X size={17} /></button></div>
      <div className="rail-section-label">Workspace</div>
      <nav className="rail-nav">{navItems.map(({ id, label, icon: Icon }) => <button key={id} className={view === id ? 'nav-item active' : 'nav-item'} onClick={() => { setView(id); setMobileNav(false) }}><Icon size={17} /><span>{label}</span>{id === 'sources' && sources.length > 0 && <small>{sources.length}</small>}</button>)}</nav>
      <div className="rail-bottom"><div className="index-card"><div className="index-card-top"><span>INDEX STATUS</span><span className="pulse" /></div><strong>{health.indexed_chunks}</strong><span>passages indexed</span></div><div className="rail-meta"><span>LOCAL WORKSPACE</span><span>v1.0.0</span></div></div>
    </aside>
    {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
    <main className="main-content">
      <header className="topbar"><button className="mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={19} /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><strong>{navItems.find((item) => item.id === view)?.label}</strong></div><div className="topbar-actions"><StatusChip mode={health.mode} /><button className="icon-button" onClick={refresh} title="Refresh workspace" aria-label="Refresh workspace"><RefreshCw size={17} /></button><button className="avatar" title="Local workspace" aria-label="Local workspace">A</button></div></header>
      <div className="content-wrap">
        {notice && <div className="notice"><Check size={15} />{notice}<button onClick={() => setNotice('')} aria-label="Dismiss notice"><X size={14} /></button></div>}
        {error && <div className="error-banner"><CircleHelp size={15} />{error}<button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button></div>}
        {view === 'research' && <section className="view view-research">
          <div className="view-heading"><div><span className="eyebrow">RESEARCH DESK / 01</span><h1>Ask the evidence.</h1><p>Search your indexed sources and get a grounded answer with a visible trail back to the text.</p></div><button className="secondary-button" onClick={() => fileInput.current?.click()}><Upload size={16} />Add sources</button></div>
          <form className="question-box" onSubmit={submitQuestion}><div className="question-label"><Sparkles size={15} /><span>Research question</span><span className="question-hint">{health.indexed_chunks ? `${health.indexed_chunks} passages available` : 'Add a source to begin'}</span></div><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What would you like to understand?" rows={3} /><div className="question-footer"><span><Paperclip size={14} />Sources stay on this device</span><button className="submit-button" type="submit" aria-label={busy ? 'Working' : 'Run research'} disabled={busy || !question.trim()}>{busy ? <LoaderCircle className="spin" size={17} /> : <Send size={16} />}<span>{busy ? 'Working' : 'Run research'}</span></button></div></form>
          {!answer ? <div className="research-empty"><EmptyState icon={Search} title="Your next finding starts here" body={health.indexed_chunks ? 'Ask a specific question and the answer will arrive with the passages that support it.' : 'Upload a PDF, DOCX, Markdown, CSV, JSON, or text file to create your first searchable index.'} action={<button className="text-button" onClick={() => fileInput.current?.click()}><Plus size={15} />Upload a source</button>} /></div> : <div className="answer-layout"><article className="answer-panel"><div className="panel-heading"><div><span className="eyebrow">ANSWER / {answer.route.toUpperCase()}</span><h2>{answer.question}</h2></div><div className="answer-tools"><span className="mode-label">{answer.mode === 'anthropic' ? 'Generated with model' : 'Synthesized locally'}</span><button className="icon-button" onClick={downloadReport} title="Download Markdown report" aria-label="Download Markdown report"><FileText size={17} /></button></div></div><div className="answer-copy"><AnswerText text={answer.answer} /></div>{answer.warnings?.length > 0 && <div className="warning-row"><CircleHelp size={15} />{answer.warnings.join(' ')}</div>}<div className="trace-row"><span>RETRIEVAL TRACE</span>{answer.retrieval_trace?.map((item) => <span className="trace-chip" key={`${item.rank}-${item.source}`}>#{item.rank} {item.source} · {item.score}</span>)}</div></article><aside className="evidence-panel"><div className="evidence-heading"><div><span className="eyebrow">EVIDENCE / {answer.citations?.length || 0} SOURCES</span><h3>Supporting passages</h3></div><BookOpen size={18} /></div>{answer.citations?.length ? <div className="citation-list">{answer.citations.map((citation) => <Citation key={citation.citation_id} citation={citation} active={selectedCitation?.citation_id === citation.citation_id} onSelect={setSelectedCitation} />)}</div> : <p className="muted-copy">No source passages were matched.</p>}<div className="excerpt-box"><span>SELECTED PASSAGE</span><p>{selectedText}</p></div></aside></div>}
        </section>}
        {view === 'sources' && <section className="view"><div className="view-heading"><div><span className="eyebrow">SOURCE LIBRARY / 02</span><h1>Your research, indexed.</h1><p>Keep source files local and inspect exactly what is available to the research desk.</p></div><button className="primary-button" onClick={() => fileInput.current?.click()}><Upload size={16} />Upload files</button></div><div className="source-toolbar"><span>{sources.length} source{sources.length === 1 ? '' : 's'} · {health.indexed_chunks} passages</span><span className="format-note">TXT · MD · PDF · DOCX · CSV · JSON</span></div>{sources.length === 0 ? <EmptyState icon={Database} title="No sources yet" body="Upload a few notes, reports, or data files and they will appear here." action={<button className="text-button" onClick={() => fileInput.current?.click()}><Plus size={15} />Add your first source</button>} /> : <div className="source-table"><div className="source-table-head"><span>Source</span><span>Type</span><span>Passages</span><span>Indexed</span></div>{sources.map((source) => <div className="source-row" key={source.source_id}><div className="source-name"><div className="file-icon"><FileText size={16} /></div><div><strong>{source.name}</strong><span>{source.size_bytes ? `${Math.round(source.size_bytes / 1024)} KB` : 'Local file'}</span></div></div><span className="type-cell">{source.file_type.replace('.', '').toUpperCase() || 'FILE'}</span><span>{source.chunk_count}</span><span className="date-cell">{new Date(source.ingested_at).toLocaleDateString()}</span></div>)}</div>}</section>}
        {view === 'activity' && <section className="view"><div className="view-heading"><div><span className="eyebrow">ACTIVITY LOG / 03</span><h1>See the trail.</h1><p>Every ingestion and research run is recorded here for review.</p></div><button className="secondary-button" onClick={refresh}><RefreshCw size={16} />Refresh log</button></div>{recentActivity.length === 0 ? <EmptyState icon={Activity} title="No activity yet" body="Your source uploads and questions will appear here as you work." /> : <div className="activity-table"><div className="activity-head"><span>Event</span><span>Message</span><span>Time</span></div>{recentActivity.map((event, index) => <div className="activity-row" key={`${event.timestamp}-${index}`}><div className="event-type"><span className={`event-mark ${event.event_type === 'query' ? 'query-mark' : 'ingest-mark'}`}>{event.event_type === 'query' ? <Search size={13} /> : <Upload size={13} />}</span><strong>{event.event_type}</strong></div><span>{event.message}</span><time>{new Date(event.timestamp).toLocaleString()}</time></div>)}</div>}</section>}
      </div>
      <footer className="footer"><span>FIELDNOTES / LOCAL RESEARCH AGENT</span><span><PanelLeft size={13} />All source material stays in your workspace</span></footer>
    </main>
    <input ref={fileInput} className="hidden-input" type="file" multiple accept=".txt,.md,.markdown,.pdf,.docx,.csv,.json" onChange={handleUpload} />
  </div>
}

export default App
