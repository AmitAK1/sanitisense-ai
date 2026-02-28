'use client';

import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import type { WardHeatmap } from '@/lib/api';

// Import leaflet CSS
import 'leaflet/dist/leaflet.css';

// Fix leaflet default icon issue in Next.js
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const RISK_COLORS: Record<string, string> = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#22c55e',
};

const RISK_FILL: Record<string, string> = {
  high: '#fecaca',
  medium: '#fef3c7',
  low: '#dcfce7',
};

// Auto-fit bounds to markers
function FitBounds({ wards }: { wards: WardHeatmap[] }) {
  const map = useMap();
  useEffect(() => {
    if (wards.length === 0) return;
    const bounds = L.latLngBounds(wards.map((w) => [w.center_lat, w.center_lng]));
    map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, wards]);
  return null;
}

interface WardMapProps {
  wards: WardHeatmap[];
  onWardClick?: (ward: WardHeatmap) => void;
  className?: string;
  height?: string;
}

export default function WardMap({ wards, onWardClick, className = '', height = '400px' }: WardMapProps) {
  if (wards.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-xl ${className}`} style={{ height }}>
        <p className="text-gray-400 text-sm">No ward data available</p>
      </div>
    );
  }

  // Mumbai center fallback
  const center: [number, number] = [19.076, 72.8777];

  return (
    <div className={`rounded-xl overflow-hidden border border-gray-200 ${className}`} style={{ height }}>
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds wards={wards} />

        {wards.map((ward) => {
          const radius = Math.max(10, Math.min(30, ward.open_reports * 2));
          return (
            <CircleMarker
              key={ward.ward_number}
              center={[ward.center_lat, ward.center_lng]}
              radius={radius}
              pathOptions={{
                color: RISK_COLORS[ward.risk_level] || '#6b7280',
                fillColor: RISK_FILL[ward.risk_level] || '#e5e7eb',
                fillOpacity: 0.6,
                weight: 2,
              }}
              eventHandlers={{
                click: () => onWardClick?.(ward),
              }}
            >
              <Popup>
                <div className="text-sm min-w-[160px]">
                  <div className="font-bold text-gray-900 mb-1">{ward.name}</div>
                  <div className="space-y-0.5 text-gray-600">
                    <div className="flex justify-between">
                      <span>Open Reports:</span>
                      <span className="font-semibold">{ward.open_reports}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Severity:</span>
                      <span className="font-semibold">{ward.severity_avg}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk Level:</span>
                      <span
                        className={`font-bold text-xs px-1.5 py-0.5 rounded ${
                          ward.risk_level === 'high'
                            ? 'bg-red-100 text-red-700'
                            : ward.risk_level === 'medium'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {ward.risk_level.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
