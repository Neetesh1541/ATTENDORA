import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, Organization, LoginRequest, RegisterRequest } from '../types';
import { authApi, organizationsApi } from '../services/api';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
  updateOrganization: (org: Organization) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'attendora_token';
const USER_KEY = 'attendora_user';
const ORG_KEY = 'attendora_org';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [organization, setOrganization] = useState<Organization | null>(() => {
    try {
      const stored = localStorage.getItem(ORG_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(ORG_KEY);
    setToken(null);
    setUser(null);
    setOrganization(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const currentUser = await authApi.getMe();
      setUser(currentUser);
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser));

      if (currentUser.organization_id) {
        try {
          const currentOrg = await organizationsApi.get(currentUser.organization_id);
          setOrganization(currentOrg);
          localStorage.setItem(ORG_KEY, JSON.stringify(currentOrg));
        } catch {
          // Non-blocking if org fetch fails
        }
      }
    } catch (error) {
      console.warn('Failed to refresh user profile:', error);
      // If 401 or network failure, interceptor or logout handles it
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, [token, refreshUser]);

  const login = async (credentials: LoginRequest): Promise<void> => {
    setIsLoading(true);
    try {
      const res = await authApi.login(credentials);
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      setToken(res.access_token);
      setUser(res.user);

      if (res.organization) {
        localStorage.setItem(ORG_KEY, JSON.stringify(res.organization));
        setOrganization(res.organization);
      } else if (res.user.organization_id) {
        try {
          const orgData = await organizationsApi.get(res.user.organization_id);
          setOrganization(orgData);
          localStorage.setItem(ORG_KEY, JSON.stringify(orgData));
        } catch {
          // ignore
        }
      }
      toast.success(`Welcome back, ${res.user.full_name}!`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Invalid email or password.';
      toast.error(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    setIsLoading(true);
    try {
      const res = await authApi.register(data);
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      setToken(res.access_token);
      setUser(res.user);

      if (res.organization) {
        localStorage.setItem(ORG_KEY, JSON.stringify(res.organization));
        setOrganization(res.organization);
      }
      toast.success('Organization registered successfully! Welcome to Attendora.');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Registration failed. Please check your details.';
      toast.error(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
  };

  const updateOrganization = (updatedOrg: Organization) => {
    setOrganization(updatedOrg);
    localStorage.setItem(ORG_KEY, JSON.stringify(updatedOrg));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        updateUser,
        updateOrganization,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
