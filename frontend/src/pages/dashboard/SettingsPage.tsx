import React, { useState } from 'react';
import { Settings as SettingsIcon, User, Building, Lock, Save, Shield } from 'lucide-react';
import { useAuth } from '../../stores/authStore';
import Card from '../../components/ui/Card';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import Tabs from '../../components/ui/Tabs';
import toast from 'react-hot-toast';

export const SettingsPage: React.FC = () => {
  const { user, organization, updateUser, updateOrganization } = useAuth();

  const [activeTab, setActiveTab] = useState<'profile' | 'organization' | 'security'>('profile');

  // Profile Form
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');

  // Org Form
  const [orgName, setOrgName] = useState(organization?.name || '');
  const [timezone, setTimezone] = useState(organization?.timezone || 'UTC');

  // Security Form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (user) {
      updateUser({ ...user, full_name: fullName, phone });
      toast.success('Profile updated successfully');
    }
  };

  const handleSaveOrg = (e: React.FormEvent) => {
    e.preventDefault();
    if (organization) {
      updateOrganization({ ...organization, name: orgName, timezone });
      toast.success('Organization settings saved');
    }
  };

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) return;
    toast.success('Security password updated');
    setCurrentPassword('');
    setNewPassword('');
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Account & Workspace Settings
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Manage your personal credentials, company profile, and security preferences.
        </p>
      </div>

      <Tabs
        tabs={[
          { id: 'profile', label: 'My Profile', icon: <User className="h-4 w-4" /> },
          { id: 'organization', label: 'Organization', icon: <Building className="h-4 w-4" /> },
          { id: 'security', label: 'Security & Auth', icon: <Lock className="h-4 w-4" /> },
        ]}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {activeTab === 'profile' && (
        <Card>
          <Card.Header>
            <Card.Title>Personal Profile</Card.Title>
            <Card.Description>Update your contact details and display name</Card.Description>
          </Card.Header>
          <Card.Content>
            <form onSubmit={handleSaveProfile} className="space-y-4 max-w-xl">
              <Input
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />

              <Input
                label="Email Address"
                value={user?.email || ''}
                disabled
                helperText="Email cannot be changed directly. Contact super admin."
              />

              <Input
                label="Phone Number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555-0100"
              />

              <Button type="submit" variant="primary" leftIcon={<Save className="h-4 w-4" />}>
                Save Changes
              </Button>
            </form>
          </Card.Content>
        </Card>
      )}

      {activeTab === 'organization' && (
        <Card>
          <Card.Header>
            <Card.Title>Organization Workspace</Card.Title>
            <Card.Description>Global settings for shifts, hours, and timezone</Card.Description>
          </Card.Header>
          <Card.Content>
            <form onSubmit={handleSaveOrg} className="space-y-4 max-w-xl">
              <Input
                label="Organization Legal Name"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                required
              />

              <Input
                label="Workspace Timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              />

              <Button type="submit" variant="primary" leftIcon={<Save className="h-4 w-4" />}>
                Save Organization Settings
              </Button>
            </form>
          </Card.Content>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card>
          <Card.Header>
            <Card.Title>Password & Authentication</Card.Title>
            <Card.Description>Ensure your administrator account uses a strong passphrase</Card.Description>
          </Card.Header>
          <Card.Content>
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-xl">
              <Input
                label="Current Password"
                type="password"
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />

              <Input
                label="New Password"
                type="password"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />

              <Button type="submit" variant="primary">
                Update Password
              </Button>
            </form>
          </Card.Content>
        </Card>
      )}
    </div>
  );
};

export default SettingsPage;
