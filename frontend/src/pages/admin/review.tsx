import Head from 'next/head';
import { useCallback, useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { apiClient } from '@/lib/api';

const LABEL_TYPES = [
  'signal',
  'update',
  'close',
  'commentary',
  'duplicate',
  'noise',
  'unresolved',
] as const;

type QueueItem = {
  raw_event_id: number;
  source_type: string;
  channel_username: string | null;
  platform_message_id: string | null;
  raw_text_preview: string | null;
  version_count: number;
  labels_count: number;
  first_seen_at: string | null;
};

function ReviewConsoleContent() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [unlabeledOnly, setUnlabeledOnly] = useState(true);
  const [editedOnly, setEditedOnly] = useState(false);
  const [outcomeBusy, setOutcomeBusy] = useState(false);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getReviewQueue({
        limit: 80,
        offset: 0,
        unlabeled_only: unlabeledOnly,
        edited_only: editedOnly,
      });
      setQueue(data.items as QueueItem[]);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки очереди');
      setQueue([]);
    } finally {
      setLoading(false);
    }
  }, [unlabeledOnly, editedOnly]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  const loadDetail = async (id: number) => {
    setSelectedId(id);
    setDetailLoading(true);
    setNotes('');
    try {
      const d = await apiClient.getRawEventDetail(id);
      setDetail(d as unknown as Record<string, unknown>);
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : 'Не удалось загрузить событие');
    } finally {
      setDetailLoading(false);
    }
  };

  const refreshDetail = async () => {
    if (selectedId == null) return;
    const d = await apiClient.getRawEventDetail(selectedId);
    setDetail(d as unknown as Record<string, unknown>);
  };

  const handleEnsureOutcomesForEvent = async () => {
    if (selectedId == null) return;
    setOutcomeBusy(true);
    setError(null);
    try {
      await apiClient.ensureSignalOutcomesForRawEvent(selectedId);
      await refreshDetail();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка ensure outcomes');
    } finally {
      setOutcomeBusy(false);
    }
  };

  const handleOutcomeStub = async (outcomeId: number) => {
    setOutcomeBusy(true);
    setError(null);
    try {
      await apiClient.postSignalOutcomeStubRecalculate(outcomeId);
      await refreshDetail();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка stub outcome');
    } finally {
      setOutcomeBusy(false);
    }
  };

  const handleOutcomeCandleRecalc = async (outcomeId: number) => {
    setOutcomeBusy(true);
    setError(null);
    try {
      await apiClient.postSignalOutcomeRecalculate(outcomeId);
      await refreshDetail();
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: unknown } } };
      const detail = ax.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : detail != null
            ? JSON.stringify(detail)
            : e instanceof Error
              ? e.message
              : 'Ошибка пересчёта по свечам';
      setError(msg);
    } finally {
      setOutcomeBusy(false);
    }
  };

  const submitLabel = async (labelType: string) => {
    if (selectedId == null) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.postReviewLabel({
        raw_event_id: selectedId,
        label_type: labelType,
        notes: notes.trim() || undefined,
      });
      setNotes('');
      await loadQueue();
      await refreshDetail();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка сохранения метки');
    } finally {
      setSaving(false);
    }
  };

  const rawEvent = detail?.raw_event as Record<string, unknown> | undefined;
  const versions =
    (detail?.message_versions as Array<Record<string, unknown>>) || [];
  const labels =
    (detail?.review_labels as Array<Record<string, unknown>>) || [];
  const extractions =
    (detail?.extractions as Array<Record<string, unknown>> | undefined) || [];
  const normalizedSignals =
    (detail?.normalized_signals as
      | Array<Record<string, unknown>>
      | undefined) || [];
  const signalRelations =
    (detail?.signal_relations as Array<Record<string, unknown>> | undefined) ||
    [];
  const signalOutcomes =
    (detail?.signal_outcomes as Array<Record<string, unknown>> | undefined) ||
    [];
  const channel = detail?.channel as
    | { username: string | null; name: string }
    | null
    | undefined;

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <Head>
        <title>Review Console — Admin</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Review Console
        </h1>
        <p className="text-sm text-gray-600 mb-6">
          Очередь raw_events (ADMIN). См. docs/REVIEW_GUIDELINES.md
        </p>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 text-red-800 text-sm px-4 py-2">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-4 mb-4 items-center">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={unlabeledOnly}
              onChange={e => setUnlabeledOnly(e.target.checked)}
            />
            Только без меток
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={editedOnly}
              onChange={e => setEditedOnly(e.target.checked)}
            />
            Только с правками (версий &gt; 1)
          </label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void loadQueue()}
          >
            Обновить
          </Button>
          <span className="text-sm text-gray-500">
            Всего в выборке: {total}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-2 border-b bg-gray-50 text-sm font-medium text-gray-700">
              Очередь
            </div>
            <div className="max-h-[70vh] overflow-y-auto">
              {loading ? (
                <p className="p-4 text-gray-500 text-sm">Загрузка…</p>
              ) : queue.length === 0 ? (
                <p className="p-4 text-gray-500 text-sm">Пусто</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {queue.map(row => (
                    <li key={row.raw_event_id}>
                      <button
                        type="button"
                        onClick={() => void loadDetail(row.raw_event_id)}
                        className={`w-full text-left px-4 py-3 text-sm hover:bg-blue-50 transition-colors ${
                          selectedId === row.raw_event_id ? 'bg-blue-50' : ''
                        }`}
                      >
                        <div className="font-mono text-xs text-gray-500">
                          #{row.raw_event_id} · {row.source_type}
                          {row.channel_username
                            ? ` · @${row.channel_username}`
                            : ''}
                          {row.platform_message_id
                            ? ` · msg ${row.platform_message_id}`
                            : ''}
                        </div>
                        <div className="text-gray-800 line-clamp-2 mt-1">
                          {row.raw_text_preview || '—'}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          версий: {row.version_count} · меток:{' '}
                          {row.labels_count}
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-2 border-b bg-gray-50 text-sm font-medium text-gray-700">
              Карточка события
            </div>
            <div className="p-4 max-h-[70vh] overflow-y-auto">
              {selectedId == null ? (
                <p className="text-gray-500 text-sm">Выберите строку слева</p>
              ) : detailLoading ? (
                <p className="text-gray-500 text-sm">Загрузка…</p>
              ) : !rawEvent ? (
                <p className="text-gray-500 text-sm">Нет данных</p>
              ) : (
                <>
                  {channel && (
                    <p className="text-sm text-gray-600 mb-2">
                      Канал: {channel.name}
                      {channel.username ? ` (@${channel.username})` : ''}
                    </p>
                  )}
                  <pre className="text-xs bg-gray-100 rounded p-3 overflow-x-auto mb-4 whitespace-pre-wrap break-words">
                    {(rawEvent.raw_text as string) || '—'}
                  </pre>
                  <div className="mb-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Версии сообщения
                    </h3>
                    <ul className="space-y-2 text-xs">
                      {versions.map(v => (
                        <li
                          key={String(v.id)}
                          className="border border-gray-100 rounded p-2 bg-gray-50"
                        >
                          <span className="font-mono text-gray-600">
                            v{v.version_no as number} ·{' '}
                            {String(v.version_reason)}
                          </span>
                          <div className="mt-1 text-gray-800 whitespace-pre-wrap">
                            {String(v.text_snapshot || '—')}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mb-4">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Метки
                    </h3>
                    {labels.length === 0 ? (
                      <p className="text-xs text-gray-400">Пока нет</p>
                    ) : (
                      <ul className="text-xs space-y-1">
                        {labels.map(l => (
                          <li key={String(l.id)} className="text-gray-700">
                            <span className="font-medium">
                              {String(l.label_type)}
                            </span>
                            {l.notes ? ` — ${String(l.notes)}` : ''}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  {(extractions.length > 0 ||
                    normalizedSignals.length > 0 ||
                    signalRelations.length > 0 ||
                    signalOutcomes.length > 0) && (
                    <div className="mb-4 space-y-4 border-t border-gray-100 pt-4">
                      {normalizedSignals.length > 0 && selectedId != null && (
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={outcomeBusy || saving}
                            onClick={() => void handleEnsureOutcomesForEvent()}
                          >
                            Слоты outcomes (все normalized)
                          </Button>
                        </div>
                      )}
                      {extractions.length > 0 && (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                            Extractions
                          </h3>
                          <ul className="space-y-2 text-xs">
                            {extractions.map(ex => {
                              const dec = ex.decision as
                                | Record<string, unknown>
                                | null
                                | undefined;
                              return (
                                <li
                                  key={String(ex.id)}
                                  className="border border-gray-100 rounded p-2 bg-slate-50"
                                >
                                  <span className="font-mono text-gray-600">
                                    #{String(ex.id)} ·{' '}
                                    {String(ex.extractor_name)}@
                                    {String(ex.extractor_version)} ·{' '}
                                    {String(ex.classification_status)}
                                  </span>
                                  {dec && (
                                    <div className="mt-1 text-gray-700">
                                      decision:{' '}
                                      <span className="font-medium">
                                        {String(dec.decision_type)}
                                      </span>
                                      {dec.confidence != null
                                        ? ` (${String(dec.confidence)})`
                                        : ''}
                                    </div>
                                  )}
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      )}
                      {normalizedSignals.length > 0 && (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                            Normalized signals
                          </h3>
                          <ul className="space-y-2 text-xs">
                            {normalizedSignals.map(ns => (
                              <li
                                key={String(ns.id)}
                                className="border border-gray-100 rounded p-2 bg-emerald-50/80"
                              >
                                <div className="font-mono text-gray-700">
                                  #{String(ns.id)} · {String(ns.asset)} ·{' '}
                                  {String(ns.direction)}
                                </div>
                                <div className="text-gray-600 mt-1">
                                  entry {String(ns.entry_price)}
                                  {ns.take_profit != null
                                    ? ` · TP ${String(ns.take_profit)}`
                                    : ''}
                                  {ns.stop_loss != null
                                    ? ` · SL ${String(ns.stop_loss)}`
                                    : ''}
                                </div>
                                {Array.isArray(ns.take_profits) &&
                                  ns.take_profits.length >= 2 && (
                                    <div className="text-gray-600 mt-0.5">
                                      TP ladder:{' '}
                                      {ns.take_profits.map(String).join(' → ')}
                                    </div>
                                  )}
                                <div className="text-gray-600 mt-1">
                                  lifecycle:{' '}
                                  <span className="font-medium">
                                    {String(ns.trading_lifecycle_status)}
                                  </span>
                                  {' · '}
                                  relation:{' '}
                                  <span className="font-medium">
                                    {String(ns.relation_status)}
                                  </span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {signalRelations.length > 0 && (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                            Signal relations
                          </h3>
                          <ul className="text-xs space-y-1 text-gray-700">
                            {signalRelations.map(rel => (
                              <li key={String(rel.id)} className="font-mono">
                                {String(rel.from_normalized_signal_id)} →{' '}
                                {String(rel.to_normalized_signal_id)} ·{' '}
                                {String(rel.relation_type)}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {signalOutcomes.length > 0 && (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                            Signal outcomes
                          </h3>
                          <ul className="space-y-2 text-xs">
                            {signalOutcomes.map(oc => (
                              <li
                                key={String(oc.id)}
                                className="border border-gray-100 rounded p-2 bg-amber-50/80"
                              >
                                <div className="flex flex-wrap items-start justify-between gap-2">
                                  <div className="min-w-0 flex-1">
                                    <div className="font-mono text-gray-700">
                                      norm #{String(oc.normalized_signal_id)} ·{' '}
                                      {String(oc.execution_model_key)}
                                    </div>
                                    <div className="text-gray-600 mt-1">
                                      status:{' '}
                                      <span className="font-medium">
                                        {String(oc.outcome_status)}
                                      </span>
                                      {oc.entry_fill_price != null
                                        ? ` · fill ${String(oc.entry_fill_price)}`
                                        : ''}
                                    </div>
                                    {oc.policy_ref != null && (
                                      <div
                                        className="text-gray-500 mt-0.5 truncate"
                                        title={String(oc.policy_ref)}
                                      >
                                        policy: {String(oc.policy_ref)}
                                      </div>
                                    )}
                                  </div>
                                  <div className="flex shrink-0 gap-1 flex-wrap justify-end">
                                    <Button
                                      type="button"
                                      variant="outline"
                                      size="sm"
                                      className="h-7 text-xs"
                                      disabled={
                                        outcomeBusy ||
                                        saving ||
                                        String(oc.outcome_status) === 'COMPLETE'
                                      }
                                      onClick={() =>
                                        void handleOutcomeCandleRecalc(
                                          Number(oc.id)
                                        )
                                      }
                                    >
                                      Свечи
                                    </Button>
                                    <Button
                                      type="button"
                                      variant="secondary"
                                      size="sm"
                                      className="h-7 text-xs"
                                      disabled={
                                        outcomeBusy ||
                                        saving ||
                                        String(oc.outcome_status) === 'COMPLETE'
                                      }
                                      onClick={() =>
                                        void handleOutcomeStub(Number(oc.id))
                                      }
                                    >
                                      Stub
                                    </Button>
                                  </div>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  <Textarea
                    placeholder="Комментарий (опционально)"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    className="mb-3 min-h-[72px] text-sm"
                  />
                  <div className="flex flex-wrap gap-2">
                    {LABEL_TYPES.map(t => (
                      <Button
                        key={t}
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={saving}
                        onClick={() => void submitLabel(t)}
                      >
                        {t}
                      </Button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminReviewPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <ReviewConsoleContent />
    </ProtectedRoute>
  );
}
