'use client';

import { useState } from 'react';
import Navbar from "@/components/Navbar";

export default function SettingsPage() {
  // الحقول تبدأ فارغة تماماً بدون أي بيانات افتراضية
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [savedMessage, setSavedMessage] = useState(false);

  // حفظ التعديلات
  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && email.trim()) {
      setSavedMessage(true);
      setTimeout(() => {
        setSavedMessage(false);
      }, 3000);
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-3xl mx-auto w-full p-6 sm:p-10">
        <div className="mb-8">
          <span className="bg-indigo-50 text-indigo-600 border border-indigo-200 text-xs px-3 py-1 rounded-full uppercase tracking-wider font-semibold">
            إعدادات الحساب
          </span>
          <h1 className="text-3xl font-extrabold mt-3 text-slate-900">
            الملف الشخصي والإعدادات
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            يمكنك تعديل بياناتك الشخصية وتفضيلات الحساب بكل سهولة.
          </p>
        </div>

        {/* رسالة النجاح عند الحفظ */}
        {savedMessage && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm">
            <span>✓</span> تم حفظ التعديلات بنجاح!
          </div>
        )}

        {/* نموذج تعديل الملف الشخصي */}
        <form onSubmit={handleSaveProfile} className="bg-slate-50 border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold text-slate-800 border-b border-slate-200 pb-3">
            معلومات الحساب الشخصي
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1.5">الاسم الكامل</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="أدخل اسمك الكامل..."
                required
                className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1.5">البريد الإلكتروني</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
                className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1.5">المادة الدراسية الأساسية المفضلة</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="أدخل المادة الأساسية..."
                className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm placeholder:text-slate-400"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition cursor-pointer shadow-sm"
            >
              حفظ التعديلات
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}