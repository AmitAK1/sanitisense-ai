'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  CheckCircle,
  Clock,
  Loader2,
  Search,
  ArrowRight,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { fetchReport, rateReport, CATEGORY_LABELS, type ReportDetail } from '@/lib/api';

interface StoredTicket {
  ticket_id: string;
  submitted_at: string;
  status: string;
}

// 4 visible stages (assigned collapses into in_progress for display)
const STATUS_STEPS = ['pending', 'in_progress', 'completed', 'verified'] as const;

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  completed: 'Completed',
  verified: 'Verified',
  unknown: 'Unknown',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700',
  assigned: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-emerald-100 text-emerald-700',
  verified: 'bg-emerald-100 text-emerald-700',
  unknown: 'bg-gray-100 text-gray-500',
};

function getStepIndex(status: string): number {
  if (status === 'verified') return 3;
  if (status === 'completed') return 2;
  if (status === 'in_progress' || status === 'assigned') return 1;
  return 0;
}

export default function TrackPage() {
  const [tickets, setTickets] = useState<StoredTicket[]>([]);
  const [reportData, setReportData] = useState<Record<string, ReportDetail | null>>({});
  const [fetchErrors, setFetchErrors] = useState<Set<string>>(new Set());
  const [fetchingIds, setFetchingIds] = useState<Set<string>>(new Set());
  const [ratedTickets, setRatedTickets] = useState<Set<string>>(new Set());
  const [pendingRatings, setPendingRatings] = useState<Record<string, number>>({});
  const [submittingRating, setSubmittingRating] = useState<string | null>(null);
  const [ratingErrors, setRatingErrors] = useState<Record<string, string>>({});
  const [manualInput, setManualInput] = useState('');
  const [manualError, setManualError] = useState('');

  // Load from localStorage once after mount (avoids SSR hydration issues)
  useEffect(() => {
    const stored = JSON.parse(
      localStorage.getItem('sanitisense_tickets') || '[]'
    ) as StoredTicket[];
    setTickets(stored);
    const rated = new Set<string>(
      JSON.parse(localStorage.getItem('sanitisense_rated') || '[]')
    );
    setRatedTickets(rated);
  }, []);

  // Fetch status for each ticket that hasn't been fetched yet
  useEffect(() => {
    tickets.forEach((t) => {
      if (reportData[t.ticket_id] === undefined && !fetchingIds.has(t.ticket_id)) {
        loadTicket(t.ticket_id);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tickets]);

  const loadTicket = async (ticketId: string) => {
    setFetchingIds((prev) => new Set(prev).add(ticketId));
    try {
      const data = await fetchReport(ticketId);
      setReportData((prev) => ({ ...prev, [ticketId]: data }));
    } catch {
      setReportData((prev) => ({ ...prev, [ticketId]: null }));
      setFetchErrors((prev) => new Set(prev).add(ticketId));
    } finally {
      setFetchingIds((prev) => {
        const next = new Set(prev);
        next.delete(ticketId);
        return next;
      });
    }
  };

  const handleAddManual = () => {
    const id = manualInput.trim().toUpperCase();
    setManualError('');
    if (!id) return;
    if (tickets.some((t) => t.ticket_id === id)) {
      setManualError('This ticket is already in your list');
      return;
    }
    const newTicket: StoredTicket = {
      ticket_id: id,
      submitted_at: new Date().toISOString(),
      status: 'unknown',
    };
    const updated = [newTicket, ...tickets];
    setTickets(updated);
    localStorage.setItem('sanitisense_tickets', JSON.stringify(updated));
    setManualInput('');
    loadTicket(id);
  };

  const handleSubmitRating = async (ticketId: string) => {
    const rating = pendingRatings[ticketId];
    if (!rating) return;
    setSubmittingRating(ticketId);
    setRatingErrors((prev) => ({ ...prev, [ticketId]: '' }));
    try {
      await rateReport(ticketId, rating);
      const newRated = new Set(ratedTickets);
      newRated.add(ticketId);
      setRatedTickets(newRated);
      localStorage.setItem('sanitisense_rated', JSON.stringify([...newRated]));
      // Refresh to show updated citizen_rating from API
      await loadTicket(ticketId);
    } catch (err) {
      setRatingErrors((prev) => ({
        ...prev,
        [ticketId]: err instanceof Error ? err.message : 'Failed to submit rating',
      }));
    } finally {
      setSubmittingRating(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Track My Reports</h1>
              <p className="text-gray-500 mt-1 text-sm">
                Check status and rate resolved complaints
              </p>
            </div>
            <Link
              href="/report"
              className="text-sm text-emerald-600 font-medium hover:underline mt-1"
            >
              + New Report
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Manual ticket lookup */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm font-medium text-gray-700 mb-3">Add a ticket by ID</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleAddManual()}
              placeholder="e.g. SANC92F31"
              maxLength={12}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono uppercase focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
            <button
              onClick={handleAddManual}
              className="px-4 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-lg hover:bg-emerald-700 flex items-center gap-1.5 transition-colors"
            >
              <Search className="h-4 w-4" />
              Track
            </button>
          </div>
          {manualError && <p className="text-xs text-red-500 mt-1.5">{manualError}</p>}
        </div>

        {/* Empty state */}
        {tickets.length === 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-10 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="h-8 w-8 text-gray-400" />
            </div>
            <p className="text-gray-600 font-medium">No reports yet</p>
            <p className="text-sm text-gray-400 mt-1">
              Submit a complaint or enter your ticket ID above
            </p>
            <Link
              href="/report"
              className="mt-4 inline-flex items-center gap-1.5 text-emerald-600 text-sm font-medium hover:underline"
            >
              Report an issue <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}

        {/* Ticket cards */}
        {tickets.map((t) => {
          const data = reportData[t.ticket_id];
          const isLoading = fetchingIds.has(t.ticket_id);
          const notFound = fetchErrors.has(t.ticket_id) && data === null;
          const status = data?.status || t.status;
          const isResolved = status === 'completed' || status === 'verified';
          const alreadyRated =
            ratedTickets.has(t.ticket_id) ||
            (data?.citizen_rating != null && data.citizen_rating > 0);
          const selectedStars = pendingRatings[t.ticket_id] || 0;
          const stepIndex = getStepIndex(status);

          return (
            <div
              key={t.ticket_id}
              className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5"
            >
              {/* Card header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="font-mono font-bold text-gray-900 text-base">
                    {t.ticket_id}
                  </span>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Submitted{' '}
                    {new Date(t.submitted_at).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </p>
                </div>
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-gray-400 mt-1" />
                ) : notFound ? (
                  <span className="text-xs text-red-500 bg-red-50 px-2.5 py-1 rounded-full">
                    Not Found
                  </span>
                ) : (
                  <span
                    className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                      STATUS_COLORS[status] || 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {STATUS_LABELS[status] || status}
                  </span>
                )}
              </div>

              {/* Report details */}
              {data && !notFound && (
                <div className="mb-4 space-y-1.5 text-sm">
                  <p className="text-gray-700">
                    <span className="text-gray-400 mr-1">Category:</span>
                    <span className="font-medium">
                      {CATEGORY_LABELS[data.category] || data.category}
                    </span>
                  </p>
                  {data.description && (
                    <p className="text-gray-500 text-xs line-clamp-2">{data.description}</p>
                  )}
                </div>
              )}

              {/* Not found message */}
              {notFound && (
                <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 rounded-lg p-3">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  Ticket not found. Please double-check the ID and try again.
                </div>
              )}

              {/* Status timeline */}
              {!notFound && (
                <>
                  <div className="flex items-center mb-1.5">
                    {STATUS_STEPS.map((s, i) => {
                      const done = i <= stepIndex;
                      const active = i === stepIndex;
                      return (
                        <div key={s} className="flex items-center flex-1">
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
                              done
                                ? active
                                  ? 'bg-emerald-600 text-white ring-2 ring-emerald-200'
                                  : 'bg-emerald-500 text-white'
                                : 'bg-gray-200 text-gray-400'
                            }`}
                          >
                            {done && !active ? (
                              <CheckCircle className="h-3.5 w-3.5" />
                            ) : active ? (
                              <div className="w-2 h-2 bg-white rounded-full" />
                            ) : (
                              <Clock className="h-3 w-3" />
                            )}
                          </div>
                          {i < STATUS_STEPS.length - 1 && (
                            <div
                              className={`flex-1 h-0.5 mx-1 transition-colors ${
                                done && i < stepIndex ? 'bg-emerald-400' : 'bg-gray-200'
                              }`}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mb-4">
                    <span>Pending</span>
                    <span>In Progress</span>
                    <span>Completed</span>
                    <span>Verified</span>
                  </div>
                </>
              )}

              {/* Star rating widget — only for resolved, not-yet-rated tickets */}
              {!notFound && isResolved && !alreadyRated && (
                <div className="border-t border-gray-100 pt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    How was the resolution?
                  </p>
                  <div className="flex gap-1 mb-3">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() =>
                          setPendingRatings((prev) => ({ ...prev, [t.ticket_id]: star }))
                        }
                        aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
                        className={`text-3xl leading-none transition-transform hover:scale-110 focus:outline-none ${
                          star <= selectedStars ? 'text-amber-400' : 'text-gray-300'
                        }`}
                      >
                        ★
                      </button>
                    ))}
                  </div>
                  {selectedStars > 0 && (
                    <button
                      onClick={() => handleSubmitRating(t.ticket_id)}
                      disabled={submittingRating === t.ticket_id}
                      className="flex items-center gap-2 px-4 py-1.5 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                    >
                      {submittingRating === t.ticket_id && (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      )}
                      Submit Rating
                    </button>
                  )}
                  {ratingErrors[t.ticket_id] && (
                    <p className="text-xs text-red-500 mt-1.5">{ratingErrors[t.ticket_id]}</p>
                  )}
                </div>
              )}

              {/* Already rated confirmation */}
              {!notFound && alreadyRated && (
                <div className="border-t border-gray-100 pt-3 flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                  <span className="text-emerald-600 font-medium">
                    Thank you for your feedback!
                  </span>
                  {data?.citizen_rating && data.citizen_rating > 0 && (
                    <span className="text-amber-400 text-base ml-auto">
                      {'★'.repeat(data.citizen_rating)}
                      {'☆'.repeat(5 - data.citizen_rating)}
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
