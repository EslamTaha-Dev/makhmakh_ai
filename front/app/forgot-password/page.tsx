'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // هنا بيتم ربط API إرسال رابط الاستعادة
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            استعادة كلمة المرور
          </h1>
          <p className="text-slate-400 text-sm mt-2">
            أدخل بريدك الإلكتروني وسنرسل لك تعليمات استعادة الحساب
          </p>
        </div>

        {submitted ? (
          <div className="bg-emerald-950/50 border border-emerald-800/50 text-emerald-300 p-4 rounded-xl text-sm text-center">
            تم إرسال تعليمات الاستعادة إلى بريدك الإلكتروني بنجاح. يرجى التحقق من صندوق الوارد.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">البريد الإلكتروني</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-xl text-sm font-medium transition cursor-pointer shadow-lg shadow-indigo-600/20 mt-2"
            >
              إرسال رابط الاستعادة
            </button>
          </form>
        )}

        <div className="text-center mt-6">
          <Link href="/login" className="text-xs text-indigo-400 hover:underline">
            العودة إلى تسجيل الدخول
          </Link>
        </div>
      </div>
    </div>
  );
}