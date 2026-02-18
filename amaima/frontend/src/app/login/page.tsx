'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogIn, UserPlus, Mail, Lock, Eye, EyeOff, ArrowLeft, KeyRound, CheckCircle, Copy } from 'lucide-react';

type Tab = 'login' | 'register' | 'forgot';

interface AuthError {
  message: string;
  field?: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [resetToken, setResetToken] = useState<string | null>(null);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [copied, setCopied] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError({
          message: data.detail || data.message || 'Login failed. Please check your credentials.',
        });
        setIsLoading(false);
        return;
      }

      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      router.push('/');
    } catch (err) {
      setError({
        message: 'An error occurred. Please try again.',
      });
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResetToken(null);

    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });

      const data = await response.json();

      if (data.reset_token) {
        setResetToken(data.reset_token);
      } else {
        setResetSuccess(true);
      }
    } catch (err) {
      setError({ message: 'An error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetWithToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError({ message: 'Passwords do not match.' });
      return;
    }
    if (formData.password.length < 8) {
      setError({ message: 'Password must be at least 8 characters long.' });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: resetToken, new_password: formData.password }),
      });

      const data = await response.json();
      if (!response.ok) {
        setError({ message: data.detail || 'Reset failed. Token may have expired.' });
        setIsLoading(false);
        return;
      }

      setResetSuccess(true);
      setResetToken(null);
    } catch (err) {
      setError({ message: 'An error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToken = () => {
    if (resetToken) {
      navigator.clipboard.writeText(resetToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError({
        message: 'Passwords do not match.',
      });
      return;
    }

    if (formData.password.length < 8) {
      setError({
        message: 'Password must be at least 8 characters long.',
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError({
          message: data.detail || data.message || 'Registration failed. Please try again.',
        });
        setIsLoading(false);
        return;
      }

      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      router.push('/');
    } catch (err) {
      setError({
        message: 'An error occurred. Please try again.',
      });
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-full blur-3xl" />
      </div>

      <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
        <a
          href="/"
          className="absolute top-6 left-6 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Home</span>
        </a>

        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2">
              <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                AMAIMA
              </span>
            </h1>
            <p className="text-slate-400">Advanced AI Orchestration Platform</p>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl overflow-hidden">
            <div className="flex border-b border-white/10">
              <button
                onClick={() => {
                  setActiveTab('login');
                  setError(null);
                  setResetToken(null);
                  setResetSuccess(false);
                  setFormData({ email: '', password: '', confirmPassword: '' });
                }}
                className={`flex-1 py-4 px-6 font-semibold text-center transition-all flex items-center justify-center gap-2 ${
                  activeTab === 'login'
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400 border-b-2 border-cyan-500'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <LogIn className="h-4 w-4" />
                <span>Login</span>
              </button>
              <button
                onClick={() => {
                  setActiveTab('register');
                  setError(null);
                  setResetToken(null);
                  setResetSuccess(false);
                  setFormData({ email: '', password: '', confirmPassword: '' });
                }}
                className={`flex-1 py-4 px-6 font-semibold text-center transition-all flex items-center justify-center gap-2 ${
                  activeTab === 'register'
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-purple-400 border-b-2 border-purple-500'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <UserPlus className="h-4 w-4" />
                <span>Register</span>
              </button>
            </div>

            <form
              onSubmit={
                activeTab === 'forgot'
                  ? (resetToken ? handleResetWithToken : handleForgotPassword)
                  : activeTab === 'login'
                    ? handleLogin
                    : handleRegister
              }
              className="p-8 space-y-5"
            >
              {activeTab === 'forgot' && resetSuccess && !resetToken ? (
                <div className="text-center space-y-4">
                  <CheckCircle className="h-12 w-12 text-green-400 mx-auto" />
                  <h3 className="text-lg font-semibold text-white">Password Reset Successful</h3>
                  <p className="text-slate-400 text-sm">
                    Your password has been reset. You can now sign in with your new password.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('login');
                      setResetSuccess(false);
                      setFormData({ email: '', password: '', confirmPassword: '' });
                    }}
                    className="w-full py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2"
                  >
                    <LogIn className="h-4 w-4" />
                    <span>Go to Login</span>
                  </button>
                </div>
              ) : activeTab === 'forgot' && resetToken ? (
                <div className="space-y-5">
                  <div className="text-center">
                    <KeyRound className="h-10 w-10 text-cyan-400 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-1">Reset Token Generated</h3>
                    <p className="text-slate-400 text-sm">Use this token to set your new password. It expires in 1 hour.</p>
                  </div>

                  <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-cyan-300 font-semibold">Your Reset Token</span>
                      <button type="button" onClick={copyToken} className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                        <Copy className="h-3 w-3" />
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <code className="block text-xs text-slate-300 bg-black/30 p-2 rounded break-all font-mono">{resetToken}</code>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="newPassword" className="block text-sm font-medium text-slate-300">New Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <input id="newPassword" type={showPassword ? 'text' : 'password'} name="password" value={formData.password} onChange={handleInputChange} required disabled={isLoading} placeholder="New password (min 8 chars)" className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all" />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-400 transition-colors">
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="confirmNewPassword" className="block text-sm font-medium text-slate-300">Confirm New Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <input id="confirmNewPassword" type={showConfirmPassword ? 'text' : 'password'} name="confirmPassword" value={formData.confirmPassword} onChange={handleInputChange} required disabled={isLoading} placeholder="Confirm new password" className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all" />
                      <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-400 transition-colors">
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">{error.message}</div>
                  )}

                  <button type="submit" disabled={isLoading} className="w-full py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2">
                    {isLoading ? (
                      <><div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" /><span>Resetting...</span></>
                    ) : (
                      <><KeyRound className="h-4 w-4" /><span>Reset Password</span></>
                    )}
                  </button>
                </div>
              ) : activeTab === 'forgot' ? (
                <div className="space-y-5">
                  <div className="text-center">
                    <KeyRound className="h-10 w-10 text-cyan-400 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-1">Forgot Your Password?</h3>
                    <p className="text-slate-400 text-sm">Enter your email address and we'll generate a reset token for you.</p>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="resetEmail" className="block text-sm font-medium text-slate-300">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <input id="resetEmail" type="email" name="email" value={formData.email} onChange={handleInputChange} required disabled={isLoading} placeholder="you@example.com" className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all" />
                    </div>
                  </div>

                  {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">{error.message}</div>
                  )}

                  <button type="submit" disabled={isLoading} className="w-full py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2">
                    {isLoading ? (
                      <><div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" /><span>Generating reset token...</span></>
                    ) : (
                      <><Mail className="h-4 w-4" /><span>Get Reset Token</span></>
                    )}
                  </button>
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <input
                        id="email"
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        required
                        disabled={isLoading}
                        placeholder="you@example.com"
                        className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                        Password
                      </label>
                      {activeTab === 'login' && (
                        <button
                          type="button"
                          onClick={() => {
                            setActiveTab('forgot');
                            setError(null);
                            setResetToken(null);
                            setResetSuccess(false);
                            setFormData({ ...formData, password: '', confirmPassword: '' });
                          }}
                          className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                        >
                          Forgot password?
                        </button>
                      )}
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        value={formData.password}
                        onChange={handleInputChange}
                        required
                        disabled={isLoading}
                        placeholder="••••••••"
                        className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-400 disabled:cursor-not-allowed transition-colors"
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {activeTab === 'register' && (
                    <div className="space-y-2">
                      <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300">
                        Confirm Password
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <input
                          id="confirmPassword"
                          type={showConfirmPassword ? 'text' : 'password'}
                          name="confirmPassword"
                          value={formData.confirmPassword}
                          onChange={handleInputChange}
                          required
                          disabled={isLoading}
                          placeholder="••••••••"
                          className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          disabled={isLoading}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-400 disabled:cursor-not-allowed transition-colors"
                        >
                          {showConfirmPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
                      {error.message}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                        <span>{activeTab === 'login' ? 'Signing in...' : 'Creating account...'}</span>
                      </>
                    ) : (
                      <>
                        {activeTab === 'login' ? (
                          <>
                            <LogIn className="h-4 w-4" />
                            <span>Sign In</span>
                          </>
                        ) : (
                          <>
                            <UserPlus className="h-4 w-4" />
                            <span>Create Account</span>
                          </>
                        )}
                      </>
                    )}
                  </button>

                  {activeTab === 'register' && (
                    <p className="text-xs text-slate-400 text-center">
                      By registering, you agree to our Terms of Service and Privacy Policy
                    </p>
                  )}
                </>
              )}
            </form>
          </div>

          <p className="text-center text-slate-400 text-sm mt-6">
            {activeTab === 'login' ? (
              <>
                Don&apos;t have an account?{' '}
                <button
                  onClick={() => setActiveTab('register')}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
                >
                  Sign up
                </button>
              </>
            ) : activeTab === 'forgot' ? (
              <>
                Remember your password?{' '}
                <button
                  onClick={() => {
                    setActiveTab('login');
                    setResetToken(null);
                    setResetSuccess(false);
                    setError(null);
                    setFormData({ email: '', password: '', confirmPassword: '' });
                  }}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
                >
                  Back to login
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  onClick={() => setActiveTab('login')}
                  className="text-purple-400 hover:text-purple-300 font-semibold transition-colors"
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
