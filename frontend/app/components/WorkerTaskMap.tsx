'use client';

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { CATEGORY_LABELS, PRIORITY_COLORS, type Task } from '@/lib/api';

interface WorkerTaskMapProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
}

export default function WorkerTaskMap({ tasks, onTaskClick }: WorkerTaskMapProps) {
  // Filter tasks that have valid lat/lng
  const mappableTasks = tasks.filter(
    (t) => t.location && parseFloat(t.location.lat) && parseFloat(t.location.lng)
  );

  if (mappableTasks.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-gray-400 text-sm">
        No tasks with location data to display on map
      </div>
    );
  }

  // Center on first task
  const center: [number, number] = [
    parseFloat(mappableTasks[0].location!.lat),
    parseFloat(mappableTasks[0].location!.lng),
  ];

  return (
    <MapContainer
      center={center}
      zoom={12}
      style={{ height: '320px', width: '100%' }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {mappableTasks.map((task) => {
        const lat = parseFloat(task.location!.lat);
        const lng = parseFloat(task.location!.lng);
        const color = PRIORITY_COLORS[task.priority] || '#6b7280';

        return (
          <CircleMarker
            key={task.task_id}
            center={[lat, lng]}
            radius={10}
            pathOptions={{
              fillColor: color,
              color: '#fff',
              weight: 2,
              fillOpacity: 0.85,
            }}
            eventHandlers={{
              click: () => onTaskClick(task),
            }}
          >
            <Popup>
              <div className="text-xs min-w-36">
                <div className="font-bold text-sm mb-1">
                  {CATEGORY_LABELS[task.category] || task.category}
                </div>
                <div className="text-gray-600">{task.description?.slice(0, 80)}...</div>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className="font-bold text-white px-1.5 py-0.5 rounded text-[10px]"
                    style={{ backgroundColor: color }}
                  >
                    {task.priority?.toUpperCase()}
                  </span>
                  <span className="text-gray-500">Ward {task.ward_number}</span>
                </div>
                <button
                  onClick={() => onTaskClick(task)}
                  className="mt-2 w-full bg-emerald-600 text-white text-xs py-1 rounded hover:bg-emerald-700"
                >
                  View Details
                </button>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
