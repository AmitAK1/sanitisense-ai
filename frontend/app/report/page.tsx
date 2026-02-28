'use client';

import { useState, useRef, useCallback } from 'react';
import {
  Camera,
  MapPin,
  Upload,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Image as ImageIcon,
  X,
  Send,
  Shield,
  Mic,
  FileText,
} from 'lucide-react';
import { submitReport, uploadImageToS3, uploadAudioToS3, CATEGORY_LABELS } from '@/lib/api';
import VoiceRecorder from '@/app/components/VoiceRecorder';
import dynamic from 'next/dynamic';

const ReportLocationMap = dynamic(() => import('@/app/components/ReportLocationMap'), { ssr: false });

type Step = 'photo' | 'location' | 'review' | 'result';

interface LocationData {
  latitude: number;
  longitude: number;
  address: string;
}

export default function ReportPage() {
  const [step, setStep] = useState<Step>('photo');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [location, setLocation] = useState<LocationData | null>(null);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [result, setResult] = useState<{
    ticket_id: string;
    ai_analysis: {
      category: string;
      severity_score: number;
      description: string;
      health_risk: string;
      confidence: number;
    };
  } | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [voiceTranscript, setVoiceTranscript] = useState('');

  // Handle image selection
  const handleImageSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be under 10MB');
      return;
    }
    setImageFile(file);
    setError('');
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
    setStep('location');
  }, []);

  // Handle drag & drop
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleImageSelect(file);
    },
    [handleImageSelect]
  );

  // Get GPS location
  const getLocation = useCallback(() => {
    setGettingLocation(true);
    setError('');
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setGettingLocation(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          address: `${pos.coords.latitude.toFixed(4)}°N, ${pos.coords.longitude.toFixed(4)}°E`,
        });
        setGettingLocation(false);
        setStep('review');
      },
      (err) => {
        // Fallback to Mumbai center if denied
        setLocation({
          latitude: 19.076,
          longitude: 72.8777,
          address: 'Mumbai, Maharashtra (default)',
        });
        setGettingLocation(false);
        setStep('review');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  // Submit report
  const handleSubmit = async () => {
    if (!imageFile || !location) return;
    setLoading(true);
    setError('');
    try {
      // Step 1: Upload image to S3 via presigned URL
      const imageKey = await uploadImageToS3(imageFile, 'citizen');

      // Step 2: Upload voice note to S3 if recorded
      let voiceKey: string | undefined;
      if (audioBlob) {
        voiceKey = await uploadAudioToS3(audioBlob);
      }

      // Step 3: Submit report with the real S3 keys
      const res = await submitReport({
        image_key: imageKey,
        latitude: location.latitude,
        longitude: location.longitude,
        ...(voiceKey && { voice_key: voiceKey }),
      });
      setResult(res);
      setStep('result');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to submit report';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Reset form
  const resetForm = () => {
    setStep('photo');
    setImageFile(null);
    setImagePreview('');
    setLocation(null);
    setDescription('');
    setResult(null);
    setError('');
    setAudioBlob(null);
    setVoiceTranscript('');
  };

  // Severity badge
  const severityColor = (score: number) => {
    if (score >= 8) return 'bg-red-100 text-red-700';
    if (score >= 5) return 'bg-amber-100 text-amber-700';
    return 'bg-green-100 text-green-700';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">Report a Sanitation Issue</h1>
          <p className="text-gray-500 mt-1">
            Upload a photo and our AI will analyze it instantly.
          </p>
        </div>
      </div>

      {/* Progress indicator */}
      <div className="max-w-2xl mx-auto px-4 py-4">
        <div className="flex items-center gap-2">
          {(['photo', 'location', 'review', 'result'] as Step[]).map((s, i) => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  step === s
                    ? 'bg-emerald-600 text-white'
                    : ['photo', 'location', 'review', 'result'].indexOf(step) > i
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {['photo', 'location', 'review', 'result'].indexOf(step) > i ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  i + 1
                )}
              </div>
              {i < 3 && (
                <div
                  className={`flex-1 h-0.5 ${
                    ['photo', 'location', 'review', 'result'].indexOf(step) > i
                      ? 'bg-emerald-400'
                      : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>Photo</span>
          <span>Location</span>
          <span>Review</span>
          <span>Result</span>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="max-w-2xl mx-auto px-4 mb-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            {error}
            <button onClick={() => setError('')} className="ml-auto">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      <div className="max-w-2xl mx-auto px-4 pb-12">
        {/* ==================== STEP 1: PHOTO ==================== */}
        {step === 'photo' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Camera className="h-5 w-5 text-emerald-600" />
              Upload Photo
            </h2>

            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-emerald-400 transition-colors cursor-pointer"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              {imagePreview ? (
                <div className="relative">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-64 mx-auto rounded-lg"
                  />
                  <button
                    className="absolute top-2 right-2 bg-white/80 rounded-full p-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      setImageFile(null);
                      setImagePreview('');
                    }}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <ImageIcon className="h-8 w-8 text-emerald-500" />
                  </div>
                  <p className="text-gray-700 font-medium mb-1">
                    Drag & drop or click to upload
                  </p>
                  <p className="text-sm text-gray-500">JPG, PNG, HEIC — Max 10MB</p>
                </>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleImageSelect(file);
              }}
            />

            {/* Camera button for mobile */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 w-full flex items-center justify-center gap-2 bg-emerald-600 text-white font-semibold py-3 rounded-xl hover:bg-emerald-700 transition-colors"
            >
              <Camera className="h-5 w-5" />
              Take Photo or Choose from Gallery
            </button>
          </div>
        )}

        {/* ==================== STEP 2: LOCATION ==================== */}
        {step === 'location' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin className="h-5 w-5 text-emerald-600" />
              Confirm Location
            </h2>

            {imagePreview && (
              <div className="mb-4 rounded-lg overflow-hidden">
                <img src={imagePreview} alt="Selected" className="w-full h-40 object-cover" />
              </div>
            )}

            <button
              onClick={getLocation}
              disabled={gettingLocation}
              className="w-full flex items-center justify-center gap-2 bg-emerald-600 text-white font-semibold py-3 rounded-xl hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              {gettingLocation ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <MapPin className="h-5 w-5" />
              )}
              {gettingLocation ? 'Getting location...' : 'Use My Current Location'}
            </button>

            {location && (
              <div className="mt-4 space-y-3">
                <ReportLocationMap
                  latitude={location.latitude}
                  longitude={location.longitude}
                  label="Your report location"
                  height="180px"
                />
                <div className="p-3 bg-emerald-50 rounded-lg text-sm text-emerald-700">
                  <span className="font-medium">Location:</span> {location.address}
                </div>
              </div>
            )}

            {/* Voice recorder */}
            <div className="mt-6">
              <VoiceRecorder
                transcript={voiceTranscript}
                onTranscript={(text) => {
                  setVoiceTranscript(text);
                  setDescription(text);
                }}
                onAudioReady={(blob) => setAudioBlob(blob)}
              />
            </div>

            {/* Optional description */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {voiceTranscript ? (
                  <span className="flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5 text-emerald-600" />
                    Transcribed Description
                    <span className="text-xs text-gray-400 font-normal">(edit if needed)</span>
                  </span>
                ) : (
                  'Additional Details (optional — or use voice above)'
                )}
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue... e.g. Near the school gate, garbage pile for 3 days"
                className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-none"
                rows={3}
              />
            </div>

            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setStep('photo')}
                className="flex-1 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={() => {
                  if (!location) {
                    getLocation();
                  } else {
                    setStep('review');
                  }
                }}
                className="flex-1 py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* ==================== STEP 3: REVIEW ==================== */}
        {step === 'review' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              Review & Submit
            </h2>

            <div className="space-y-4">
              {imagePreview && (
                <img
                  src={imagePreview}
                  alt="Report"
                  className="w-full h-48 object-cover rounded-lg"
                />
              )}

              {location && (
                <ReportLocationMap
                  latitude={location.latitude}
                  longitude={location.longitude}
                  label="Report location"
                  height="160px"
                />
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="text-gray-500">Latitude</span>
                  <div className="font-medium">{location?.latitude.toFixed(6)}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="text-gray-500">Longitude</span>
                  <div className="font-medium">{location?.longitude.toFixed(6)}</div>
                </div>
              </div>

              {location?.address && (
                <div className="bg-gray-50 p-3 rounded-lg text-sm">
                  <span className="text-gray-500">Address</span>
                  <div className="font-medium">{location.address}</div>
                </div>
              )}

              {description && (
                <div className="bg-gray-50 p-3 rounded-lg text-sm">
                  <span className="text-gray-500">Description</span>
                  <div className="font-medium">{description}</div>
                </div>
              )}

              {audioBlob && (
                <div className="bg-purple-50 p-3 rounded-lg text-sm flex items-center gap-2">
                  <Mic className="h-4 w-4 text-purple-600" />
                  <span className="text-purple-700 font-medium">Voice note attached</span>
                  <span className="text-purple-400 text-xs">({(audioBlob.size / 1024).toFixed(0)} KB)</span>
                </div>
              )}
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-4 text-sm text-amber-700 flex items-start gap-2">
              <Shield className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                Your report will be analyzed by <strong>Amazon Bedrock AI</strong> to classify the
                issue type, severity, and health risk automatically.
                {audioBlob && ' Your voice description will be included as supporting evidence.'}
              </span>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep('location')}
                className="flex-1 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
                {loading ? 'Analyzing...' : 'Submit Report'}
              </button>
            </div>
          </div>
        )}

        {/* ==================== STEP 4: RESULT ==================== */}
        {step === 'result' && result && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="h-8 w-8 text-emerald-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Report Submitted!</h2>
              <p className="text-gray-500 mt-1">AI analysis complete</p>
            </div>

            {/* Ticket ID */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center mb-6">
              <div className="text-sm text-emerald-600 mb-1">Your Ticket ID</div>
              <div className="text-2xl font-bold text-emerald-700 font-mono">
                {result.ticket_id}
              </div>
            </div>

            {/* AI Analysis */}
            <h3 className="font-semibold text-gray-900 mb-3">AI Analysis Results</h3>

            {/* Report Location on Map */}
            {location && (
              <div className="mb-4">
                <ReportLocationMap
                  latitude={location.latitude}
                  longitude={location.longitude}
                  label={`${result.ticket_id} — ${CATEGORY_LABELS[result.ai_analysis.category] || result.ai_analysis.category}`}
                  height="200px"
                />
                <p className="text-xs text-gray-400 mt-1 text-center">
                  📍 {location.latitude.toFixed(5)}°N, {location.longitude.toFixed(5)}°E
                </p>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-500">Category</span>
                <span className="font-medium text-sm">
                  {CATEGORY_LABELS[result.ai_analysis.category] || result.ai_analysis.category}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-500">Severity</span>
                <span
                  className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${severityColor(
                    result.ai_analysis.severity_score
                  )}`}
                >
                  {result.ai_analysis.severity_score}/10
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-500">Health Risk</span>
                <span className="font-medium text-sm capitalize">
                  {result.ai_analysis.health_risk}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-500">AI Confidence</span>
                <span className="font-medium text-sm">
                  {(result.ai_analysis.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-500 block mb-1">AI Description</span>
                <p className="text-sm text-gray-700">{result.ai_analysis.description}</p>
              </div>
            </div>

            <button
              onClick={resetForm}
              className="mt-6 w-full flex items-center justify-center gap-2 bg-emerald-600 text-white font-semibold py-3 rounded-xl hover:bg-emerald-700"
            >
              <Camera className="h-5 w-5" />
              Report Another Issue
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
