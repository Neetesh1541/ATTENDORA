import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';
import { useAuth } from '../../stores/authStore';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';

export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});

  const validate = (): boolean => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await login({ email, password });
      navigate('/dashboard');
    } catch (err: any) {
      setErrors((prev) => ({
        ...prev,
        general: err.response?.data?.detail || 'Incorrect email or password. Please try again.',
      }));
    }
  };

  // Demo fill helper for quick testing
  const handleQuickDemo = (role: 'admin' | 'user') => {
    if (role === 'admin') {
      setEmail('admin@attendora.ai');
      setPassword('Admin@123456');
    } else {
      setEmail('manager@attendora.ai');
      setPassword('Manager@123456');
    }
    setErrors({});
  };

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Welcome back
        </h2>
        <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          Sign in to your Attendora organization account to continue.
        </p>
      </div>

      {errors.general && (
        <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-400">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email Address"
          type="email"
          placeholder="admin@company.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
          }}
          error={errors.email}
          leftIcon={<Mail className="h-4 w-4" />}
          autoComplete="email"
          autoFocus
        />

        <div>
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
            }}
            error={errors.password}
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
            autoComplete="current-password"
          />

          <div className="mt-2 flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 cursor-pointer select-none text-slate-600 dark:text-slate-400">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800"
              />
              <span>Remember me</span>
            </label>

            <button
              type="button"
              onClick={() => alert('Password reset link will be sent to your registered organization email.')}
              className="font-medium text-brand-600 hover:text-brand-500 dark:text-brand-400"
            >
              Forgot password?
            </button>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          Sign In
        </Button>
      </form>

      {/* Demo Credentials Helper */}
      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-xs dark:border-slate-800 dark:bg-slate-850">
        <p className="font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
          Quick Demo Accounts:
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleQuickDemo('admin')}
            className="flex-1 rounded-lg border border-slate-200 bg-white py-1.5 px-2 text-[11px] font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
          >
            Admin Demo
          </button>
          <button
            type="button"
            onClick={() => handleQuickDemo('user')}
            className="flex-1 rounded-lg border border-slate-200 bg-white py-1.5 px-2 text-[11px] font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
          >
            Manager Demo
          </button>
        </div>
      </div>

      <div className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
        Don&apos;t have an organization account?{' '}
        <Link
          to="/register"
          className="font-semibold text-brand-600 hover:text-brand-500 dark:text-brand-400"
        >
          Create Organization
        </Link>
      </div>
    </div>
  );
};

export default LoginPage;
