import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { kbAPI, type KBChunk, type KBPromotion, type KBAudit } from '@/lib/api';

function message(error: unknown): string {
  return (error as { response?: { data?: { detail?: string } }; message?: string })
    ?.response?.data?.detail || (error as Error)?.message || 'Request failed';
}

export default function KnowledgeBase({ admin }: { admin: boolean }) {
  const [chunks, setChunks] = useState<KBChunk[]>([]);
  const [promotions, setPromotions] = useState<KBPromotion[]>([]);
  const [audit, setAudit] = useState<KBAudit[]>([]);
  const [review, setReview] = useState<KBPromotion | null>(null);
  const [selected, setSelected] = useState<KBChunk | null>(null);
  const [versions, setVersions] = useState<Array<{ version_id: string; content: string; created_at: string; status: string }>>([]);
  const [content, setContent] = useState('');
  const [query, setQuery] = useState('');
  const [draft, setDraft] = useState('');
  const [expiry, setExpiry] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [items, requests] = await Promise.all([kbAPI.list(), kbAPI.promotions()]);
      setChunks(items);
      setPromotions(requests);
      if (admin) setAudit(await kbAPI.audit());
    } catch (error) {
      toast.error(message(error));
    }
  }, [admin]);

  useEffect(() => { void load(); }, [load]);

  const select = async (chunk: KBChunk) => {
    setSelected(chunk);
    setDraft(chunk.content);
    try {
      const view = await kbAPI.history(chunk.chunk_id);
      setVersions(view.versions);
    } catch (error) {
      setVersions([]);
      toast.error(message(error));
    }
  };

  const act = async (action: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await action();
      toast.success('Memory updated');
      await load();
      setSelected(null);
      setVersions([]);
    } catch (error) {
      toast.error(message(error));
    } finally {
      setBusy(false);
    }
  };

  const search = async () => {
    setBusy(true);
    try {
      setChunks(await kbAPI.search(query));
    } catch (error) {
      toast.error(message(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5 text-[#171717]">
      <section className="rounded-xl border border-[#171717]/10 bg-white p-4 space-y-3">
        <h2 className="font-semibold">Versioned knowledge</h2>
        <div className="flex flex-wrap gap-2">
          <Input aria-label="Search knowledge" placeholder="Search authorized memory" className="max-w-md" value={query} onChange={e => setQuery(e.target.value)} />
          <Button variant="outline" disabled={!query.trim() || busy} onClick={() => void search()}>Search</Button>
          <Button variant="outline" onClick={() => void load()}>Show all</Button>
        </div>
        <Textarea aria-label="New knowledge" placeholder="Add a private learning" value={content} onChange={e => setContent(e.target.value)} />
        <Button disabled={!content.trim() || busy} onClick={() => act(async () => { await kbAPI.create(content); setContent(''); })}>Add private memory</Button>
      </section>
      {admin && <section className="rounded-xl border border-[#171717]/10 bg-white p-4 space-y-2">
        <h2 className="font-semibold">Governance audit</h2>
        {audit.slice(0, 20).map((event, index) => <p key={`${event.created_at}-${index}`} className="text-xs break-words">
          {new Date(event.created_at).toLocaleString()} · {event.action} · {event.chunk_id || event.request_id || '—'}
        </p>)}
      </section>}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-[#171717]/10 bg-white p-4 space-y-2">
          <h2 className="font-semibold">Available memories</h2>
          {chunks.length === 0 && <p className="text-sm text-[#171717]/55">No active chunks in your enabled scopes.</p>}
          {chunks.map(chunk => (
            <button key={chunk.chunk_id} type="button" onClick={() => void select(chunk)}
              className="block w-full rounded-lg border border-[#171717]/10 p-3 text-left hover:border-[#756200] focus-visible:outline-2">
              <span className="text-xs font-semibold">{chunk.scope} · {chunk.chunk_type} · weight {chunk.memory_weight.toFixed(2)}</span>
              <p className="mt-1 text-sm line-clamp-3 whitespace-pre-wrap">{chunk.content}</p>
            </button>
          ))}
        </section>
        <section className="rounded-xl border border-[#171717]/10 bg-white p-4 space-y-3">
          <h2 className="font-semibold">{selected ? 'Memory history and publication' : 'Select a memory'}</h2>
          {selected && <>
            <p className="text-xs text-[#171717]/55">{selected.chunk_id} · {selected.scope}</p>
            <ol className="space-y-2 text-sm max-h-52 overflow-y-auto">
              {versions.map((version, index) => <li key={version.version_id} className="rounded-lg bg-[#f8f8f6] p-2">
                <span className="text-xs">Version {index + 1} · {version.status} · {new Date(version.created_at).toLocaleString()}</span>
                <p className="whitespace-pre-wrap">{version.content}</p>
              </li>)}
            </ol>
            {selected.scope === 'USER' && <>
              <Textarea aria-label="Memory draft" value={draft} onChange={e => setDraft(e.target.value)} />
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy || !draft.trim()} onClick={() => act(() => kbAPI.append(selected, draft))}>Append version</Button>
                <Button variant="outline" disabled={busy || !draft.trim()} onClick={() => act(() => kbAPI.request(selected.chunk_id, 'AGENT', draft))}>Request global promotion</Button>
              </div>
              <p className="text-xs text-[#171717]/55">For global publication, remove private details and describe reusable guidance. An admin must approve it.</p>
            </>}
            {admin && selected.scope !== 'USER' && <>
              <label htmlFor="kb-expiry" className="block text-xs font-medium">Expiry (optional)</label>
              <Input id="kb-expiry" type="datetime-local" value={expiry} onChange={e => setExpiry(e.target.value)} />
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" disabled={busy} onClick={() => act(() => kbAPI.expiry(selected.chunk_id, expiry ? new Date(expiry).toISOString() : null))}>Set expiry</Button>
                <Button variant="destructive" disabled={busy} onClick={() => act(() => kbAPI.revoke(selected.chunk_id))}>Revoke published memory</Button>
              </div>
            </>}
          </>}
        </section>
      </div>

      <section className="rounded-xl border border-[#171717]/10 bg-white p-4 space-y-3">
        <h2 className="font-semibold">{admin ? 'Promotion review' : 'Your promotion requests'}</h2>
        {promotions.length === 0 && <p className="text-sm text-[#171717]/55">No requests yet.</p>}
        {promotions.map(request => <div key={request.request_id} className="rounded-lg border border-[#171717]/10 p-3 space-y-2">
          <p className="text-xs font-semibold">{request.from_scope} → {request.to_scope} · {request.state}</p>
          {review?.request_id === request.request_id && <p className="text-sm whitespace-pre-wrap">{review.proposed_content}</p>}
          <div className="flex flex-wrap gap-2">
            {!admin && <Button variant="outline" disabled={busy} onClick={async () => {
              try { setReview(await kbAPI.promotion(request.request_id)); }
              catch (error) { toast.error(message(error)); }
            }}>View details</Button>}
            {admin && request.state === 'APPROVAL_PENDING' && <>
              <Button variant="outline" disabled={busy} onClick={async () => {
                try { setReview(await kbAPI.promotion(request.request_id)); }
                catch (error) { toast.error(message(error)); }
              }}>Review details</Button>
              {review?.request_id === request.request_id && <>
                <Button disabled={busy} onClick={() => act(() => kbAPI.review(request.request_id, true))}>Approve</Button>
                <Button variant="outline" disabled={busy} onClick={() => act(() => kbAPI.review(request.request_id, false))}>Reject</Button>
              </>}
            </>}
            {request.state === 'APPROVAL_PENDING' && <Button variant="outline" disabled={busy} onClick={() => act(() => kbAPI.cancel(request.request_id))}>Cancel</Button>}
            {admin && request.target_chunk_id && request.state === 'TARGET_ACTIVE' && <Button variant="destructive" disabled={busy} onClick={() => act(() => kbAPI.demote(request.target_chunk_id!))}>Demote</Button>}
          </div>
        </div>)}
      </section>
    </div>
  );
}
