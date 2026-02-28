'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Square, Play, Pause, RotateCcw, Globe, Loader2 } from 'lucide-react';

// ── Supported languages for speech recognition ──────────────────────────────
const LANGUAGES = [
  { code: 'en-IN', label: 'English', name: 'English' },
  { code: 'hi-IN', label: 'हिंदी', name: 'Hindi' },
  { code: 'mr-IN', label: 'मराठी', name: 'Marathi' },
  { code: 'ta-IN', label: 'தமிழ்', name: 'Tamil' },
  { code: 'te-IN', label: 'తెలుగు', name: 'Telugu' },
  { code: 'bn-IN', label: 'বাংলা', name: 'Bengali' },
  { code: 'gu-IN', label: 'ગુજરાતી', name: 'Gujarati' },
];

interface VoiceRecorderProps {
  /** Called whenever transcription changes (live + final) */
  onTranscript: (text: string) => void;
  /** Called when recording finishes with the audio blob */
  onAudioReady: (blob: Blob) => void;
  /** Optional: current transcript text (controlled) */
  transcript?: string;
}

export default function VoiceRecorder({ onTranscript, onAudioReady, transcript = '' }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [language, setLanguage] = useState('en-IN');
  const [showLangPicker, setShowLangPicker] = useState(false);
  const [supported, setSupported] = useState(true);
  const [liveText, setLiveText] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const finalTranscriptRef = useRef('');

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition || !navigator.mediaDevices?.getUserMedia) {
      setSupported(false);
    }
  }, []);

  // Timer for recording duration
  useEffect(() => {
    if (isRecording && !isPaused) {
      timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isRecording, isPaused]);

  // Format seconds → mm:ss
  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  // ── Start Recording ───────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // MediaRecorder for audio capture
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
          ? 'audio/webm;codecs=opus' 
          : 'audio/webm',
      });
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        onAudioReady(blob);
        // Stop all tracks
        stream.getTracks().forEach((t) => t.stop());
      };
      
      mediaRecorder.start(1000); // collect chunks every second
      mediaRecorderRef.current = mediaRecorder;

      // SpeechRecognition for live transcription
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language;
        recognition.maxAlternatives = 1;
        
        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interim = '';
          let final = finalTranscriptRef.current;
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              final += result[0].transcript + ' ';
              finalTranscriptRef.current = final;
            } else {
              interim += result[0].transcript;
            }
          }
          
          const fullText = (final + interim).trim();
          setLiveText(interim);
          onTranscript(fullText);
        };
        
        recognition.onerror = (e: SpeechRecognitionErrorEvent) => {
          console.warn('Speech recognition error:', e.error);
          // Don't stop recording on transient errors
          if (e.error === 'not-allowed') {
            console.error('Microphone permission denied for speech recognition');
          }
        };
        
        recognition.onend = () => {
          // Auto-restart if still recording (recognition can time out)
          if (mediaRecorderRef.current?.state === 'recording') {
            try { recognition.start(); } catch { /* ignore */ }
          }
        };
        
        recognition.start();
        recognitionRef.current = recognition;
      }

      setIsRecording(true);
      setIsPaused(false);
      setDuration(0);
      setAudioUrl(null);
      finalTranscriptRef.current = transcript ? transcript + ' ' : '';
      setLiveText('');
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  }, [language, onAudioReady, onTranscript, transcript]);

  // ── Stop Recording ────────────────────────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state !== 'inactive') {
      mediaRecorderRef.current?.stop();
    }
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setIsRecording(false);
    setIsPaused(false);
    setLiveText('');
  }, []);

  // ── Reset ─────────────────────────────────────────────────────────────────
  const resetRecording = useCallback(() => {
    stopRecording();
    setDuration(0);
    setAudioUrl(null);
    finalTranscriptRef.current = '';
    setLiveText('');
    onTranscript('');
  }, [stopRecording, onTranscript]);

  // ── Play/Pause audio ─────────────────────────────────────────────────────
  const togglePlayback = useCallback(() => {
    if (!audioUrl) return;
    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl);
      audioRef.current.onended = () => setIsPlaying(false);
    }
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }, [audioUrl, isPlaying]);

  // ── Not supported fallback ────────────────────────────────────────────────
  if (!supported) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700">
        <p className="font-medium">Voice recording not supported</p>
        <p className="mt-1">Please use Chrome, Edge, or Safari for voice input. You can still type your description below.</p>
      </div>
    );
  }

  const selectedLang = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];

  return (
    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
      {/* Header with language picker */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Mic className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-semibold text-purple-800">Voice Description</span>
          <span className="text-xs text-purple-500">(in your language)</span>
        </div>
        
        {/* Language selector */}
        <div className="relative">
          <button
            onClick={() => setShowLangPicker(!showLangPicker)}
            disabled={isRecording}
            className="flex items-center gap-1.5 text-xs bg-white border border-purple-200 rounded-lg px-2.5 py-1.5 text-purple-700 hover:bg-purple-50 disabled:opacity-50"
          >
            <Globe className="h-3 w-3" />
            {selectedLang.label}
          </button>
          
          {showLangPicker && (
            <div className="absolute right-0 top-full mt-1 bg-white border border-purple-200 rounded-lg shadow-lg z-10 min-w-[140px]">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => { setLanguage(lang.code); setShowLangPicker(false); }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-purple-50 first:rounded-t-lg last:rounded-b-lg ${
                    language === lang.code ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-700'
                  }`}
                >
                  {lang.label} <span className="text-gray-400 text-xs">({lang.name})</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recording controls */}
      <div className="flex items-center gap-3">
        {!isRecording && !audioUrl && (
          <button
            onClick={startRecording}
            className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2.5 rounded-xl font-medium text-sm hover:bg-purple-700 transition-colors shadow-sm"
          >
            <Mic className="h-4 w-4" />
            Start Recording
          </button>
        )}

        {isRecording && (
          <>
            {/* Recording indicator + timer */}
            <div className="flex items-center gap-2 bg-red-100 text-red-700 px-3 py-2 rounded-xl text-sm font-medium">
              <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
              {formatTime(duration)}
            </div>
            
            <button
              onClick={stopRecording}
              className="flex items-center gap-1.5 bg-gray-800 text-white px-3 py-2 rounded-xl text-sm font-medium hover:bg-gray-900"
            >
              <Square className="h-3.5 w-3.5 fill-current" />
              Stop
            </button>
          </>
        )}

        {!isRecording && audioUrl && (
          <>
            <button
              onClick={togglePlayback}
              className="flex items-center gap-1.5 bg-white border border-purple-200 text-purple-700 px-3 py-2 rounded-xl text-sm font-medium hover:bg-purple-50"
            >
              {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>
            
            <span className="text-xs text-gray-500">{formatTime(duration)}</span>
            
            <button
              onClick={resetRecording}
              className="flex items-center gap-1.5 text-gray-500 hover:text-red-600 px-2 py-2 text-sm"
              title="Re-record"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </>
        )}

        {/* Max duration hint */}
        {isRecording && duration >= 50 && (
          <span className="text-xs text-amber-600 font-medium">Max 60s</span>
        )}
      </div>

      {/* Auto-stop at 60 seconds */}
      {isRecording && duration >= 60 && (() => { stopRecording(); return null; })()}

      {/* Live transcription preview */}
      {(isRecording && liveText) && (
        <div className="mt-3 p-2.5 bg-white/60 rounded-lg border border-purple-100">
          <div className="flex items-center gap-1.5 mb-1">
            <Loader2 className="h-3 w-3 text-purple-500 animate-spin" />
            <span className="text-xs text-purple-500 font-medium">Transcribing...</span>
          </div>
          <p className="text-sm text-gray-600 italic">{liveText}</p>
        </div>
      )}

      {/* Info text */}
      {!isRecording && !audioUrl && (
        <p className="mt-2.5 text-xs text-purple-500">
          Speak in any supported language to describe the problem. Your voice will be converted to text automatically and attached to the report.
        </p>
      )}

      {audioUrl && (
        <p className="mt-2.5 text-xs text-emerald-600 font-medium">
          ✓ Voice note recorded. Transcribed text shown in description below.
        </p>
      )}
    </div>
  );
}
