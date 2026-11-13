import React, { useState, useEffect } from 'react';
import { Camera as CameraIcon, Plus, Video, Wifi, WifiOff, Trash2, Edit2, Play } from 'lucide-react';
import { camerasApi } from '../../services/api';
import { Camera, CameraStatus } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import toast from 'react-hot-toast';

export const CamerasPage: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([
    {
      id: 'cam-1',
      organization_id: 'org1',
      name: 'Main Entrance Lobby A',
      location: 'Ground Floor, Building 1',
      camera_type: 'rtsp',
      stream_url: 'rtsp://192.168.1.100:554/stream1',
      status: 'online',
      is_active: true,
      last_active: '2026-11-13T09:12:00Z',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'cam-2',
      organization_id: 'org1',
      name: 'South Turnstile Kiosk',
      location: 'South Gate Security Gatehouse',
      camera_type: 'webcam',
      stream_url: '',
      status: 'online',
      is_active: true,
      last_active: '2026-11-13T09:11:45Z',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'cam-3',
      organization_id: 'org1',
      name: 'Cafeteria & Breakroom',
      location: 'Level 3 East Wing',
      camera_type: 'ip',
      stream_url: 'http://192.168.1.102/video.mjpg',
      status: 'offline',
      is_active: true,
      last_active: '2026-11-12T18:00:00Z',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ]);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newCamera, setNewCamera] = useState({
    name: '',
    location: '',
    camera_type: 'webcam',
    stream_url: '',
  });
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleAddCamera = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCamera.name) return;

    const created: Camera = {
      id: `cam-${Date.now()}`,
      organization_id: 'org1',
      name: newCamera.name,
      location: newCamera.location,
      camera_type: newCamera.camera_type,
      stream_url: newCamera.stream_url,
      status: 'online',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setCameras([...cameras, created]);
    toast.success(`Camera ${created.name} connected`);
    setIsAddModalOpen(false);
    setNewCamera({ name: '', location: '', camera_type: 'webcam', stream_url: '' });
  };

  const toggleStatus = (id: string) => {
    setCameras((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, status: (c.status === 'online' ? 'offline' : 'online') as CameraStatus } : c
      )
    );
  };

  const handleDelete = () => {
    if (!deleteId) return;
    setCameras((prev) => prev.filter((c) => c.id !== deleteId));
    toast.success('Camera disconnected');
    setDeleteId(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Camera Streams & Vision Terminals
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Configure RTSP endpoints, USB kiosks, and live recognition zones.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => setIsAddModalOpen(true)}
        >
          Add Camera Node
        </Button>
      </div>

      {/* Grid of Cameras */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cameras.map((cam) => (
          <Card key={cam.id} className="overflow-hidden">
            <div className="relative aspect-video w-full bg-slate-900 flex items-center justify-center">
              <CameraIcon className="h-12 w-12 text-slate-700" />
              <div className="absolute top-3 left-3">
                <Badge
                  color={cam.status === 'online' ? 'green' : 'red'}
                  variant="dot"
                >
                  {cam.status.toUpperCase()}
                </Badge>
              </div>

              <div className="absolute bottom-3 right-3">
                <span className="rounded-md bg-slate-950/80 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                  {cam.camera_type.toUpperCase()}
                </span>
              </div>
            </div>

            <Card.Content className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                    {cam.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">{cam.location}</p>
                </div>
              </div>

              {cam.stream_url && (
                <p className="mt-3 truncate font-mono text-[11px] text-slate-500 bg-slate-50 dark:bg-slate-800 p-2 rounded-lg">
                  {cam.stream_url}
                </p>
              )}

              <div className="mt-5 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => toggleStatus(cam.id)}
                >
                  {cam.status === 'online' ? 'Take Offline' : 'Connect'}
                </Button>

                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDeleteId(cam.id)}
                >
                  <Trash2 className="h-4 w-4 text-rose-500" />
                </Button>
              </div>
            </Card.Content>
          </Card>
        ))}
      </div>

      {/* Add Camera Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Register New Camera Endpoint"
        description="Provide the connection URI or select local USB capture."
      >
        <form onSubmit={handleAddCamera} className="space-y-4 mt-2">
          <Input
            label="Camera Name"
            placeholder="e.g. West Gate Turnstile"
            value={newCamera.name}
            onChange={(e) => setNewCamera({ ...newCamera, name: e.target.value })}
            required
          />

          <Input
            label="Physical Location"
            placeholder="e.g. Level 1 Reception"
            value={newCamera.location}
            onChange={(e) => setNewCamera({ ...newCamera, location: e.target.value })}
          />

          <Select
            label="Camera Protocol"
            value={newCamera.camera_type}
            onChange={(e) => setNewCamera({ ...newCamera, camera_type: e.target.value })}
            options={[
              { value: 'webcam', label: 'USB / Built-in Webcam' },
              { value: 'rtsp', label: 'RTSP IP Camera Stream' },
              { value: 'ip', label: 'HTTP / MJPEG Camera Stream' },
            ]}
          />

          {newCamera.camera_type !== 'webcam' && (
            <Input
              label="Stream URL"
              placeholder="rtsp://admin:pass@192.168.1.10:554/live"
              value={newCamera.stream_url}
              onChange={(e) => setNewCamera({ ...newCamera, stream_url: e.target.value })}
            />
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Register Camera
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Remove Camera?"
        description="Removing this camera will stop automatic attendance detection from this node."
      />
    </div>
  );
};

export default CamerasPage;
