'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import {
  ClipboardList,
  CheckCircle,
  Clock,
  AlertTriangle,
  Camera,
  ChevronRight,
  Loader2,
  X,
  Upload,
  User,
  MapPin,
  Filter,
  Image as ImageIcon,
  ShieldCheck,
  Navigation,
} from 'lucide-react';
import {
  fetchTasks,
  updateTask,
  uploadImageToS3,
  validateCompletion,
  CATEGORY_LABELS,
  PRIORITY_COLORS,
  STATUS_COLORS,
  type Task,
} from '@/lib/api';

const WorkerTaskMap = dynamic(() => import('@/app/components/WorkerTaskMap'), { ssr: false });

export default function WorkerDashboard() {
  const [workerId, setWorkerId] = useState('W-001');

  // Read localStorage only on client after mount to avoid hydration mismatch
  useEffect(() => {
    const stored = localStorage.getItem('sanitisense_worker_id');
    if (stored) setWorkerId(stored);
  }, []);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('pending');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [updating, setUpdating] = useState(false);
  const [afterPhoto, setAfterPhoto] = useState<string>('');
  const [afterPhotoFile, setAfterPhotoFile] = useState<File | null>(null);
  const [workerNotes, setWorkerNotes] = useState('');
  const [validationResult, setValidationResult] = useState<Record<string, unknown> | null>(null);
  const [showMap, setShowMap] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [bypassMode, setBypassMode] = useState(false);
  const [bypassReason, setBypassReason] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const S3_BASE = 'https://sanitisense-media-982253889131.s3.us-east-1.amazonaws.com';

  // Load tasks
  useEffect(() => {
    loadTasks();
  }, [filterStatus]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await fetchTasks(filterStatus);
      setTasks(data);
    } catch {
      // Fallback demo data if API fails
      setTasks(getDemoTasks(filterStatus));
    } finally {
      setLoading(false);
    }
  };

  // Update task status — with S3 upload + validation for completion
  const handleStatusUpdate = async (taskId: string, newStatus: string) => {
    setUpdating(true);
    setValidationResult(null);
    try {
      if (newStatus === 'completed' && bypassMode) {
        // Camera bypass — mark completed, flag for admin review
        const reason = bypassReason.trim() || 'Camera unavailable';
        await updateTask(taskId, {
          status: 'completed',
          notes: `BYPASS: ${reason}`,
        });
        setSelectedTask(null);
        setWorkerNotes('');
        setAfterPhoto('');
        setAfterPhotoFile(null);
        setValidationResult(null);
        setBypassMode(false);
        setBypassReason('');
        setTasks([]);
        setFilterStatus('completed');
        return;
      }

      if (newStatus === 'completed' && afterPhotoFile && selectedTask?.image_key) {
        // Step 1: Upload after-photo to S3
        const afterKey = await uploadImageToS3(afterPhotoFile, 'worker');

        // Step 2: Update task with completed status
        await updateTask(taskId, { status: 'completed', notes: workerNotes });

        // Step 3: Call validation endpoint (before/after AI comparison)
        setIsValidating(true);
        try {
          const validation = await validateCompletion({
            task_id: taskId,
            before_image_key: selectedTask.image_key,
            after_image_key: afterKey,
          });
          setValidationResult(validation as unknown as Record<string, unknown>);
          // Don't close modal — show validation result
          loadTasks();
          return;
        } catch {
          // Validation call failed but task is still marked complete
          console.warn('Validation API call failed, task still marked complete');
        } finally {
          setIsValidating(false);
        }
      } else {
        // Simple status update (start task, etc.)
        await updateTask(taskId, { status: newStatus, notes: workerNotes, worker_id: workerId });
      }
      // Close modal and switch to the new status tab
      // The useEffect on filterStatus will re-fetch the correct list
      setSelectedTask(null);
      setWorkerNotes('');
      setAfterPhoto('');
      setAfterPhotoFile(null);
      setValidationResult(null);
      setBypassMode(false);
      setBypassReason('');
      setTasks([]);  // Clear stale list so user sees loading spinner
      setFilterStatus(newStatus);
    } catch {
      // API call failed — optimistic update for demo, still switch tab
      setSelectedTask(null);
      setTasks([]);
      setFilterStatus(newStatus);
    } finally {
      setUpdating(false);
    }
  };

  // Handle after photo — keep both File (for S3 upload) and base64 (for preview)
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAfterPhotoFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => setAfterPhoto(ev.target?.result as string);
      reader.readAsDataURL(file);
      // Automatically exit bypass mode if user uploads a photo
      setBypassMode(false);
      setBypassReason('');
    }
  };

  const priorityLabel = (p: string) => {
    const labels: Record<string, string> = {
      critical: 'CRITICAL',
      high: 'HIGH',
      medium: 'MED',
      low: 'LOW',
    };
    return labels[p] || p;
  };

  const statusCounts = {
    pending: tasks.length,
    in_progress: 0,
    completed: 0,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Worker Dashboard</h1>
              <p className="text-gray-500 text-sm mt-0.5">Field task management</p>
            </div>
            <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1.5 rounded-lg">
              <User className="h-4 w-4 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-700">{workerId}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* View toggle: List | Map */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex gap-2 overflow-x-auto pb-2 flex-1">
            {['pending', 'assigned', 'in_progress', 'completed'].map((status) => {
              const label = status === 'completed' ? 'Completed / Verified'
                : status.replace('_', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
              return (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${filterStatus === status
                    ? 'bg-emerald-600 text-white'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                    }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setShowMap(!showMap)}
            className={`ml-2 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${showMap
              ? 'bg-emerald-600 text-white'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
          >
            {showMap ? <ClipboardList className="h-4 w-4" /> : <Navigation className="h-4 w-4" />}
            {showMap ? 'List' : 'Map'}
          </button>
        </div>

        {/* Map view */}
        {showMap && tasks.length > 0 && (
          <div className="mb-6 bg-white rounded-xl border border-gray-200 overflow-hidden">
            <WorkerTaskMap
              tasks={tasks}
              onTaskClick={(task) => setSelectedTask(task)}
            />
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          </div>
        )}

        {/* Empty state */}
        {!loading && tasks.length === 0 && (
          <div className="text-center py-20 bg-white rounded-2xl border border-gray-200">
            <ClipboardList className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No {filterStatus.replace('_', ' ')} tasks</p>
            <p className="text-sm text-gray-400 mt-1">Try a different filter</p>
          </div>
        )}

        {/* Task list */}
        {!loading && tasks.length > 0 && (
          <div className="space-y-3">
            {tasks.map((task, idx) => (
              <div
                key={task.task_id || `task-${idx}`}
                onClick={() => setSelectedTask(task)}
                className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
                        style={{
                          backgroundColor: PRIORITY_COLORS[task.priority] || '#6b7280',
                        }}
                      >
                        {priorityLabel(task.priority)}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">{task.task_id}</span>
                      {task.report_id && (
                        <span className="text-xs text-emerald-600 font-mono bg-emerald-50 px-1.5 py-0.5 rounded">
                          {task.report_id}
                        </span>
                      )}
                    </div>
                    <h3 className="font-medium text-gray-900 text-sm">
                      {CATEGORY_LABELS[task.category] || task.category}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {task.description}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        Ward {task.ward_number}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        SLA: {task.sla_hours}h
                      </span>
                      <span
                        className="font-medium px-1.5 py-0.5 rounded text-xs"
                        style={{
                          backgroundColor: STATUS_COLORS[task.status] + '20',
                          color: STATUS_COLORS[task.status],
                        }}
                      >
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-300 mt-1" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task detail modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between rounded-t-2xl">
              <h2 className="font-bold text-gray-900">Task Details</h2>
              <button
                onClick={() => {
                  setSelectedTask(null);
                  setAfterPhoto('');
                  setAfterPhotoFile(null);
                  setWorkerNotes('');
                  setValidationResult(null);
                }}
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Citizen's before-photo */}
              {selectedTask.image_key && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                    <ImageIcon className="h-4 w-4 text-red-500" />
                    Reported Issue (Before)
                  </label>
                  <img
                    src={`${S3_BASE}/${selectedTask.image_key}`}
                    alt="Reported issue"
                    className="w-full h-44 object-cover rounded-lg border border-gray-200"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                </div>
              )}

              {/* Task info */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Task ID</span>
                  <span className="font-mono font-medium">{selectedTask.task_id}</span>
                </div>
                {selectedTask.report_id && (
                  <div className="flex justify-between text-sm items-center">
                    <span className="text-gray-500">Citizen Ticket</span>
                    <span className="font-mono font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      {selectedTask.report_id}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Category</span>
                  <span className="font-medium">
                    {CATEGORY_LABELS[selectedTask.category] || selectedTask.category}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Priority</span>
                  <span
                    className="font-bold text-xs px-2 py-0.5 rounded-full text-white"
                    style={{
                      backgroundColor: PRIORITY_COLORS[selectedTask.priority] || '#6b7280',
                    }}
                  >
                    {selectedTask.priority.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Severity</span>
                  <span className="font-medium">{selectedTask.severity_score}/10</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Ward</span>
                  <span className="font-medium">Ward {selectedTask.ward_number}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">SLA</span>
                  <span className="font-medium">{selectedTask.sla_hours} hours</span>
                </div>
              </div>

              {/* Navigate button */}
              {selectedTask.location && (
                <a
                  href={`https://maps.google.com/?daddr=${selectedTask.location.lat},${selectedTask.location.lng}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 active:scale-95 transition-all"
                >
                  <Navigation className="h-4 w-4" />
                  Navigate to Location
                </a>
              )}

              <div className="bg-gray-50 p-3 rounded-lg text-sm">
                <span className="text-gray-500 block mb-1">Description</span>
                <p className="text-gray-700">{selectedTask.description}</p>
              </div>

              {/* After photo upload + bypass (for completing) */}
              {selectedTask.status !== 'completed' && selectedTask.status !== 'verified' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Completion Photo
                      <span className="ml-1 text-red-500">*</span>
                    </label>
                    {afterPhoto ? (
                      <div className="relative">
                        <img
                          src={afterPhoto}
                          alt="After"
                          className="w-full h-40 object-cover rounded-lg"
                        />
                        <button
                          onClick={() => { setAfterPhoto(''); setAfterPhotoFile(null); }}
                          className="absolute top-2 right-2 bg-white/80 rounded-full p-1"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => fileRef.current?.click()}
                        disabled={bypassMode}
                        className={`w-full border-2 border-dashed rounded-lg p-6 text-center transition ${bypassMode
                            ? 'border-gray-200 opacity-40 cursor-not-allowed'
                            : 'border-gray-300 hover:border-emerald-400'
                          }`}
                      >
                        <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">Take or upload after photo</p>
                        <p className="text-xs text-gray-400 mt-1">Required to mark task complete</p>
                      </button>
                    )}
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                      onChange={handlePhotoUpload}
                    />

                    {/* Camera bypass toggle */}
                    {!afterPhotoFile && !bypassMode && (
                      <button
                        onClick={() => setBypassMode(true)}
                        className="mt-2 text-xs text-gray-400 hover:text-amber-600 underline"
                      >
                        📷 Camera not working?
                      </button>
                    )}

                    {/* Bypass reason form */}
                    {bypassMode && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-xs font-medium text-amber-800 mb-2">
                          🚩 Bypass mode — task will be flagged for admin review
                        </p>
                        <textarea
                          value={bypassReason}
                          onChange={(e) => setBypassReason(e.target.value)}
                          placeholder="Briefly explain why a photo couldn't be taken..."
                          className="w-full border border-amber-300 rounded-lg p-2 text-xs focus:ring-2 focus:ring-amber-400 outline-none resize-none"
                          rows={2}
                        />
                        <button
                          onClick={() => { setBypassMode(false); setBypassReason(''); }}
                          className="text-xs text-gray-400 hover:text-gray-600 underline mt-1"
                        >
                          Cancel bypass
                        </button>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notes
                    </label>
                    <textarea
                      value={workerNotes}
                      onChange={(e) => setWorkerNotes(e.target.value)}
                      placeholder="Add notes about the task..."
                      className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-none"
                      rows={2}
                    />
                  </div>
                </>
              )}

              {/* Action buttons */}
              <div className="flex gap-3 pt-2">
                {selectedTask.status === 'pending' && (
                  <button
                    onClick={() => handleStatusUpdate(selectedTask.task_id, 'in_progress')}
                    disabled={updating || isValidating}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updating ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
                    Start Task
                  </button>
                )}
                {selectedTask.status === 'assigned' && (
                  <button
                    onClick={() => handleStatusUpdate(selectedTask.task_id, 'in_progress')}
                    disabled={updating || isValidating}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updating ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
                    Start Task
                  </button>
                )}
                {selectedTask.status === 'in_progress' && (
                  isValidating ? (
                    <div className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-purple-50 text-purple-700 font-semibold border border-purple-200">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      AI is reviewing…
                    </div>
                  ) : (
                    <button
                      onClick={() => handleStatusUpdate(selectedTask.task_id, 'completed')}
                      disabled={updating || (!afterPhotoFile && !bypassMode)}
                      title={!afterPhotoFile && !bypassMode ? 'Upload a completion photo first' : undefined}
                      className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {updating ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <CheckCircle className="h-5 w-5" />
                      )}
                      {bypassMode ? 'Submit (Bypass)' : 'Mark Complete'}
                    </button>
                  )
                )}
                {selectedTask.status === 'completed' && (
                  <div className="flex-1 text-center py-3 bg-amber-50 text-amber-700 rounded-xl font-medium border border-amber-200">
                    <Loader2 className="h-5 w-5 inline mr-2 animate-spin" />
                    Awaiting AI Verification
                  </div>
                )}
                {selectedTask.status === 'verified' && (
                  <div className="flex-1 text-center py-3 bg-emerald-50 text-emerald-700 rounded-xl font-medium border border-emerald-200">
                    <CheckCircle className="h-5 w-5 inline mr-2" />
                    ✅ Verified by AI
                  </div>
                )}
                {selectedTask.status === 'rejected' && (
                  <div className="flex-1 text-center py-3 bg-red-50 text-red-700 rounded-xl font-medium border border-red-200">
                    ❌ Rejected — Needs Redo
                  </div>
                )}
              </div>

              {/* AI Validation Result */}
              {validationResult && (
                <div className="border border-purple-200 bg-purple-50 rounded-xl p-4 space-y-2">
                  <h4 className="font-semibold text-purple-800 flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5" />
                    AI Verification Result
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500">Status:</span>{' '}
                      <span className="font-semibold capitalize">
                        {String((validationResult as Record<string, unknown>).new_status || 'pending')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Score:</span>{' '}
                      <span className="font-semibold">
                        {String(((validationResult as Record<string, Record<string, unknown>>).validation || {}).resolution_score || '-')}/10
                      </span>
                    </div>
                  </div>
                  {((validationResult as Record<string, Record<string, unknown>>).validation || {}).observations ? (
                    <p className="text-sm text-purple-700 mt-1">
                      {String(((validationResult as Record<string, Record<string, unknown>>).validation || {}).observations)}
                    </p>
                  ) : null}
                  <button
                    onClick={() => {
                      setSelectedTask(null);
                      setAfterPhoto('');
                      setAfterPhotoFile(null);
                      setWorkerNotes('');
                      setValidationResult(null);
                    }}
                    className="w-full mt-2 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Demo tasks fallback
function getDemoTasks(status: string): Task[] {
  const categories = ['garbage_pile', 'overflowing_drain', 'blocked_sewer', 'stagnant_water', 'medical_waste'];
  const priorities = ['critical', 'high', 'medium', 'low'];

  return Array.from({ length: 8 }, (_, i) => ({
    task_id: `TSK-260301-${String(i + 1).padStart(3, '0')}`,
    report_id: `RPT-${i + 100}`,
    status,
    priority: priorities[i % 4],
    sla_hours: [4, 12, 24, 48][i % 4],
    category: categories[i % 5],
    severity_score: 9 - i,
    description: [
      'Large garbage pile near school entrance blocking pedestrian access',
      'Overflowing drain causing waterlogging on main road',
      'Blocked sewer line causing sewage backflow in residential area',
      'Stagnant water near children\'s playground — mosquito breeding risk',
      'Medical waste found dumped near public park area',
      'Garbage accumulation at market junction for over a week',
      'Drain overflow causing damage to adjacent shop foundations',
      'Old construction debris mixed with household waste',
    ][i],
    ward_number: (i % 24) + 1,
    assigned_worker_id: status === 'pending' ? null : 'W-001',
    created_at: new Date(Date.now() - i * 3600000).toISOString(),
    updated_at: new Date(Date.now() - i * 1800000).toISOString(),
  }));
}
