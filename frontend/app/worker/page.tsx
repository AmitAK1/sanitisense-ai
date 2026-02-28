'use client';

import { useState, useEffect, useRef } from 'react';
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
} from 'lucide-react';
import {
  fetchTasks,
  updateTask,
  CATEGORY_LABELS,
  PRIORITY_COLORS,
  STATUS_COLORS,
  type Task,
} from '@/lib/api';

const WORKER_ID = 'W-001'; // Demo worker

export default function WorkerDashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('pending');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [updating, setUpdating] = useState(false);
  const [afterPhoto, setAfterPhoto] = useState<string>('');
  const [workerNotes, setWorkerNotes] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

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

  // Update task status
  const handleStatusUpdate = async (taskId: string, newStatus: string) => {
    setUpdating(true);
    try {
      await updateTask(taskId, { status: newStatus, notes: workerNotes });
      setSelectedTask(null);
      setWorkerNotes('');
      setAfterPhoto('');
      loadTasks();
    } catch {
      // Optimistic update for demo
      setTasks((prev) =>
        prev.map((t) => (t.task_id === taskId ? { ...t, status: newStatus } : t))
      );
      setSelectedTask(null);
    } finally {
      setUpdating(false);
    }
  };

  // Handle after photo
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setAfterPhoto(ev.target?.result as string);
      reader.readAsDataURL(file);
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
              <span className="text-sm font-medium text-emerald-700">{WORKER_ID}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Filter tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['pending', 'assigned', 'in_progress', 'completed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                filterStatus === status
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>

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
            {tasks.map((task) => (
              <div
                key={task.task_id}
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
                  setWorkerNotes('');
                }}
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Task info */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Task ID</span>
                  <span className="font-mono font-medium">{selectedTask.task_id}</span>
                </div>
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

              <div className="bg-gray-50 p-3 rounded-lg text-sm">
                <span className="text-gray-500 block mb-1">Description</span>
                <p className="text-gray-700">{selectedTask.description}</p>
              </div>

              {/* After photo upload (for completing) */}
              {selectedTask.status !== 'completed' && selectedTask.status !== 'verified' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Upload Completion Photo
                    </label>
                    {afterPhoto ? (
                      <div className="relative">
                        <img
                          src={afterPhoto}
                          alt="After"
                          className="w-full h-40 object-cover rounded-lg"
                        />
                        <button
                          onClick={() => setAfterPhoto('')}
                          className="absolute top-2 right-2 bg-white/80 rounded-full p-1"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => fileRef.current?.click()}
                        className="w-full border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-emerald-400 transition"
                      >
                        <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">Take or upload after photo</p>
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
                    disabled={updating}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updating ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
                    Start Task
                  </button>
                )}
                {selectedTask.status === 'assigned' && (
                  <button
                    onClick={() => handleStatusUpdate(selectedTask.task_id, 'in_progress')}
                    disabled={updating}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updating ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
                    Start Task
                  </button>
                )}
                {selectedTask.status === 'in_progress' && (
                  <button
                    onClick={() => handleStatusUpdate(selectedTask.task_id, 'completed')}
                    disabled={updating}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {updating ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <CheckCircle className="h-5 w-5" />
                    )}
                    Mark Complete
                  </button>
                )}
                {selectedTask.status === 'completed' && (
                  <div className="flex-1 text-center py-3 bg-emerald-50 text-emerald-700 rounded-xl font-medium">
                    <CheckCircle className="h-5 w-5 inline mr-2" />
                    Task Completed — Awaiting AI Verification
                  </div>
                )}
              </div>
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
