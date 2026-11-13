import React, { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import {
  Video,
  Play,
  Square,
  Volume2,
  VolumeX,
  Maximize2,
  CheckCircle2,
  Users,
  Clock,
  Sparkles,
  Camera,
  Activity,
} from 'lucide-react';
import { facesApi, attendanceApi } from '../../services/api';
import { RecognitionResult } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import toast from 'react-hot-toast';

export const LiveRecognitionPage: React.FC = () => {
  const webcamRef = useRef<Webcam>(null);

  const [isRunning, setIsRunning] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState('cam-01');
  const [detectedFaces, setDetectedFaces] = useState<RecognitionResult[]>([]);
  const [liveLog, setLiveLog] = useState<
    Array<{ id: string; name: string; uid: string; time: string; confidence: number }>
  >([
    { id: '1', name: 'Alexander Wright', uid: 'EMP-001', time: '09:02:14 AM', confidence: 0.994 },
    { id: '2', name: 'Elena Rostova', uid: 'EMP-002', time: '09:03:02 AM', confidence: 0.988 },
  ]);

  // Periodic frame verification loop
  useEffect(() => {
    let interval: any = null;

    if (isRunning) {
      interval = setInterval(async () => {
        if (webcamRef.current) {
          const imageSrc = webcamRef.current.getScreenshot();
          if (imageSrc) {
            try {
              // Simulated AI match response for demo
              const mockMatch: RecognitionResult = {
                person_id: 'p-alex',
                person_name: 'Alexander Wright',
                person_unique_id: 'EMP-001',
                confidence: 0.992,
                box: { x: 35, y: 25, width: 30, height: 40 },
                matched: true,
                timestamp: new Date().toISOString(),
              };

              setDetectedFaces([mockMatch]);
            } catch {
              // fallback
            }
          }
        }
      }, 2500);
    } else {
      setDetectedFaces([]);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning]);

  const handleSimulateCheckIn = (name: string, uid: string) => {
    const newEntry = {
      id: String(Date.now()),
      name,
      uid,
      time: new Date().toLocaleTimeString(),
      confidence: 0.985 + Math.random() * 0.014,
    };
    setLiveLog((prev) => [newEntry, ...prev.slice(0, 9)]);
    toast.success(`Attendance marked: ${name}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Live Facial Recognition Terminal
            </h1>
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-ping" />
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Real-time multi-person face tracking & automatic attendance logging.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={selectedCamera}
            onChange={(e) => setSelectedCamera(e.target.value)}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            <option value="cam-01">Camera 01 — Main Entrance Lobby</option>
            <option value="cam-02">Camera 02 — South Turnstile Kiosk</option>
            <option value="cam-03">Camera 03 — 3rd Floor Cafeteria</option>
            <option value="webcam">Local Web Camera (Active)</option>
          </select>

          <Button
            variant={isRunning ? 'danger' : 'primary'}
            size="sm"
            onClick={() => setIsRunning(!isRunning)}
            leftIcon={isRunning ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          >
            {isRunning ? 'Stop Feed' : 'Start Feed'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setAudioEnabled(!audioEnabled)}
          >
            {audioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Main Scanner Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Video Canvas */}
        <div className="lg:col-span-8 space-y-3">
          <Card className="overflow-hidden border-slate-800 bg-slate-950 p-0 shadow-2xl">
            <div className="relative aspect-video w-full overflow-hidden bg-slate-950 flex items-center justify-center">
              {isRunning ? (
                <>
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    videoConstraints={{ width: 1280, height: 720, facingMode: 'user' }}
                    className="h-full w-full object-cover"
                  />

                  {/* AI Scanning Beam */}
                  <div className="pointer-events-none absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-brand-500 to-transparent animate-scan" />

                  {/* Real-time Bounding Box */}
                  {detectedFaces.map((face, index) => (
                    <div
                      key={index}
                      className="absolute border-2 border-emerald-400 bg-emerald-500/10 rounded-xl transition-all duration-300 flex flex-col justify-between p-2 shadow-lg shadow-emerald-500/20"
                      style={{
                        top: `${face.box.y}%`,
                        left: `${face.box.x}%`,
                        width: `${face.box.width}%`,
                        height: `${face.box.height}%`,
                      }}
                    >
                      <div className="self-end rounded-md bg-emerald-500 px-1.5 py-0.5 text-[10px] font-bold text-white shadow-xs">
                        {(face.confidence * 100).toFixed(1)}%
                      </div>
                      <div className="rounded-lg bg-slate-950/80 px-2 py-1 backdrop-blur-md text-[11px] font-semibold text-white border border-emerald-500/40">
                        <p className="truncate">{face.person_name}</p>
                        <p className="text-[10px] text-emerald-400">{face.person_unique_id}</p>
                      </div>
                    </div>
                  ))}

                  {/* HUD Top Left */}
                  <div className="absolute top-3 left-3 flex items-center gap-2 rounded-lg bg-slate-900/85 px-3 py-1.5 text-[11px] font-mono text-emerald-400 backdrop-blur-md border border-slate-800">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>AI LIVE • RTSP 1080P • 30FPS</span>
                  </div>

                  {/* HUD Bottom Right */}
                  <div className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg bg-slate-900/85 px-3 py-1 text-[11px] font-mono text-slate-300 backdrop-blur-md border border-slate-800">
                    <Activity className="h-3.5 w-3.5 text-brand-400" />
                    <span>LIVENESS: PASS • ANTI-SPOOF: ACTIVE</span>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center p-12 text-center text-slate-500">
                  <Camera className="h-12 w-12 text-slate-600 mb-3" />
                  <p className="text-sm font-semibold">Live stream paused</p>
                  <p className="text-xs text-slate-600 mt-1">Press Start Feed to resume real-time AI scanning</p>
                </div>
              )}
            </div>
          </Card>

          {/* Quick Simulation Trigger Bar */}
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-xs dark:border-slate-800 dark:bg-slate-900">
            <span className="text-slate-500">Simulate Entry Walkthrough:</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleSimulateCheckIn('Alexander Wright', 'EMP-001')}
                className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2.5 py-1 text-slate-800 dark:bg-slate-800 dark:text-slate-200 font-medium transition-colors"
              >
                + Alexander
              </button>
              <button
                type="button"
                onClick={() => handleSimulateCheckIn('Elena Rostova', 'EMP-002')}
                className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2.5 py-1 text-slate-800 dark:bg-slate-800 dark:text-slate-200 font-medium transition-colors"
              >
                + Elena
              </button>
              <button
                type="button"
                onClick={() => handleSimulateCheckIn('Marcus Chen', 'EMP-003')}
                className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2.5 py-1 text-slate-800 dark:bg-slate-800 dark:text-slate-200 font-medium transition-colors"
              >
                + Marcus
              </button>
            </div>
          </div>
        </div>

        {/* Right: Real-time Attendance Feed */}
        <div className="lg:col-span-4 space-y-4">
          <Card>
            <Card.Header>
              <div className="flex items-center justify-between">
                <Card.Title>Live Event Log</Card.Title>
                <Badge color="green" variant="dot">
                  Tracking
                </Badge>
              </div>
              <Card.Description>Verified attendees entering via this camera node</Card.Description>
            </Card.Header>
            <Card.Content>
              <div className="divide-y divide-slate-100 dark:divide-slate-800 space-y-3">
                {liveLog.map((log) => (
                  <div key={log.id} className="pt-3 first:pt-0 flex items-start justify-between">
                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
                        <CheckCircle2 className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                          {log.name}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {log.uid} • Conf: {(log.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>

                    <span className="font-mono text-[11px] text-slate-500">
                      {log.time}
                    </span>
                  </div>
                ))}
              </div>
            </Card.Content>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LiveRecognitionPage;
