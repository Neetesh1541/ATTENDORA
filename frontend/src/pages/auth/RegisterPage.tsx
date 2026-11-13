import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Building2, User, Mail, Lock, Phone, Globe, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../stores/authStore';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Button from '../../components/ui/Button';

const orgTypes = [
  { value: 'corporate', label: 'Corporate Office / Tech Enterprise' },
  { value: 'school', label: 'School / K-12 Academy' },
  { value: 'university', label: 'College / University Campus' },
  { value: 'factory', label: 'Factory / Manufacturing Plant' },
  { value: 'hospital', label: 'Hospital / Healthcare Center' },
  { value: 'retail', label: 'Retail Chain / Superstore' },
  { value: 'gym', label: 'Gym & Fitness Center' },
  { value: 'general', label: 'General Organization' },
  { value: 'other', label: 'Other Enterprise' },
];

const timezones = [
  { value: 'UTC', label: 'UTC (Universal Coordinated Time)' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'Europe/London', label: 'London, Edinburgh, Dublin (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Central European Time (Paris, Berlin)' },
  { value: 'Asia/Kolkata', label: 'India Standard Time (IST)' },
  { value: 'Asia/Tokyo', label: 'Japan Standard Time (JST)' },
  { value: 'Asia/Singapore', label: 'Singapore, Hong Kong, Beijing' },
  { value: 'Australia/Sydney', label: 'Sydney, Melbourne (AEST)' },
];

export const RegisterPage: React.FC = () => {
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    org_name: '',
    org_type: 'corporate',
    timezone: 'UTC',
    phone: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    confirm_password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.org_name.trim() || formData.org_name.length < 2) {
      newErrors.org_name = 'Organization name must be at least 2 characters';
    }

    if (!formData.admin_name.trim() || formData.admin_name.length < 2) {
      newErrors.admin_name = 'Admin full name is required';
    }

    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Admin email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Please enter a valid email address';
    }

    if (!formData.admin_password) {
      newErrors.admin_password = 'Password is required';
    } else if (formData.admin_password.length < 8) {
      newErrors.admin_password = 'Password must be at least 8 characters';
    }

    if (formData.admin_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    if (!agreedToTerms) {
      newErrors.terms = 'You must agree to the Terms of Service & Privacy Policy';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await register({
        org_name: formData.org_name,
        org_type: formData.org_type,
        timezone: formData.timezone,
        phone: formData.phone || undefined,
        admin_name: formData.admin_name,
        admin_email: formData.admin_email,
        admin_password: formData.admin_password,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setErrors((prev) => ({
        ...prev,
        general:
          err.response?.data?.detail ||
          'Failed to register organization. Email might already be registered.',
      }));
    }
  };

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Create Organization
        </h2>
        <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          Set up your organization workspace and primary administrator account.
        </p>
      </div>

      {errors.general && (
        <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-400">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Organization Section */}
        <div className="space-y-3">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Organization Details
          </p>

          <Input
            label="Organization Name"
            placeholder="e.g. Acme Technologies Inc."
            value={formData.org_name}
            onChange={(e) => setFormData({ ...formData, org_name: e.target.value })}
            error={errors.org_name}
            leftIcon={<Building2 className="h-4 w-4" />}
            autoFocus
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Select
              label="Organization Type"
              options={orgTypes}
              value={formData.org_type}
              onChange={(e) => setFormData({ ...formData, org_type: e.target.value })}
            />

            <Select
              label="Timezone"
              options={timezones}
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
            />
          </div>

          <Input
            label="Contact Phone (Optional)"
            placeholder="+1 (555) 000-0000"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            leftIcon={<Phone className="h-4 w-4" />}
          />
        </div>

        {/* Administrator Section */}
        <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Primary Administrator
          </p>

          <Input
            label="Admin Full Name"
            placeholder="Johnathan Doe"
            value={formData.admin_name}
            onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
            error={errors.admin_name}
            leftIcon={<User className="h-4 w-4" />}
          />

          <Input
            label="Work Email Address"
            type="email"
            placeholder="admin@company.com"
            value={formData.admin_email}
            onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
            error={errors.admin_email}
            leftIcon={<Mail className="h-4 w-4" />}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Password (min 8 chars)"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={formData.admin_password}
              onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
              error={errors.admin_password}
              leftIcon={<Lock className="h-4 w-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
            />

            <Input
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={formData.confirm_password}
              onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
              error={errors.confirm_password}
              leftIcon={<Lock className="h-4 w-4" />}
            />
          </div>
        </div>

        {/* Terms checkbox */}
        <div className="pt-2">
          <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none">
            <input
              type="checkbox"
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800"
            />
            <span>
              I agree to the Attendora{' '}
              <a href="#" className="font-medium text-brand-600 underline hover:text-brand-500 dark:text-brand-400">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="font-medium text-brand-600 underline hover:text-brand-500 dark:text-brand-400">
                Privacy Policy
              </a>
              .
            </span>
          </label>
          {errors.terms && (
            <p className="mt-1 text-xs font-medium text-rose-500">{errors.terms}</p>
          )}
        </div>

        <div className="pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={isLoading}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            Create Organization Workspace
          </Button>
        </div>
      </form>

      <div className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
        Already registered?{' '}
        <Link
          to="/login"
          className="font-semibold text-brand-600 hover:text-brand-500 dark:text-brand-400"
        >
          Sign in here
        </Link>
      </div>
    </div>
  );
};

export default RegisterPage;
