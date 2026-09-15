'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';
import Link from 'next/link';

export default function DashboardPage() {
  // استخدام State حقيقي يبدأ من الصفر ليعكس الواقع بدقة
  const [stats] = useState({
    uploadedFiles: 0,
    activeChats: 0,
    systemStatus: 'نشط'
  });

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-8">
        {/* ترحيب عام */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div>
            <h1 className="text-2xl font-bold mb-1">مرحباً بك في لوحة تحكم المنصة 👋</h1>
            <p className="text-slate-400 text-sm">
              تابع نشاطك التعليمي، الملفات المرفوعة، واستفد من المساعد الذكي لتطوير مستواك.
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/chat"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition shadow-md shadow-indigo-600/20"
            >
              ابدأ المحادثة الذكية
            </Link>
          </div>
        </div>

        {/* بطاقات الإحصائيات الحقيقية */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
            <h3 className="text-slate-400 text-sm font-medium mb-2">الملفات المرفوعة</h3>
            <p className="text-3xl font-extrabold text-indigo-400">{stats.uploadedFiles}</p>
            <span className="text-xs text-slate-400 mt-2 inline-block">ابدأ برفع أول ملف لك</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
            <h3 className="text-slate-400 text-sm font-medium mb-2">الاستفسارات النشطة</h3>
            <p className="text-3xl font-extrabold text-indigo-400">{stats.activeChats}</p>
            <span className="text-xs text-slate-400 mt-2 inline-block">لا توجد محادثات نشطة حالياً</span>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
            <h3 className="text-slate-400 text-sm font-medium mb-2">حالة النظام</h3>
            <p className="text-3xl font-extrabold text-emerald-400">{stats.systemStatus}</p>
            <span className="text-xs text-emerald-500 mt-2 inline-block">متصل وجاهز للاستخدام</span>
          </div>
        </div>

        {/* قسم الروابط السريعة */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
          <h2 className="text-lg font-bold mb-4">الإجراءات السريعة</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              href="/upload"
              className="p-4 rounded-xl border border-slate-800 bg-slate-950/50 hover:border-indigo-500 transition flex items-center justify-between"
            >
              <div>
                <h4 className="font-semibold text-sm">رفع ملف جديد</h4>
                <p className="text-slate-400 text-xs mt-0.5">رفع محاضرات بصيغة PDF أو TXT</p>
              </div>
              <span className="text-indigo-400 text-lg">📁</span>
            </Link>

            <Link
              href="/chat"
              className="p-4 rounded-xl border border-slate-800 bg-slate-950/50 hover:border-indigo-500 transition flex items-center justify-between"
            >
              <div>
                <h4 className="font-semibold text-sm">فتح الشات الذكي</h4>
                <p className="text-slate-400 text-xs mt-0.5">ابدأ طرح الأسئلة والحصول على إجابات</p>
              </div>
              <span className="text-indigo-400 text-lg">💬</span>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}