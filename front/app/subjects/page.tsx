'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function SubjectsPage() {
  const [availableSubjects, setAvailableSubjects] = useState([
    'الذكاء الاصطناعي (AI)',
    'هندسة البرمجيات',
    'قواعد البيانات (Databases)',
    'الشبكات وأمن المعلومات',
    'تراكيب البيانات والخوارزميات'
  ]);
  
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>([]);
  const [customSubject, setCustomSubject] = useState('');

  // تبديل اختيار المادة (إضافة أو إزالة)
  const toggleSubject = (subject: string) => {
    if (selectedSubjects.includes(subject)) {
      setSelectedSubjects(selectedSubjects.filter(s => s !== subject));
    } else {
      setSelectedSubjects([...selectedSubjects, subject]);
    }
  };

  // إضافة مادة جديدة من قِبل الطالب
  const handleAddCustomSubject = (e: React.FormEvent) => {
    e.preventDefault();
    if (customSubject.trim() && !availableSubjects.includes(customSubject)) {
      setAvailableSubjects([...availableSubjects, customSubject.trim()]);
      setSelectedSubjects([...selectedSubjects, customSubject.trim()]);
      setCustomSubject('');
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 p-6 sm:p-10">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <span className="bg-indigo-50 text-indigo-600 border border-indigo-200 text-xs px-3 py-1 rounded-full uppercase tracking-wider font-semibold">
            خطوة تخصيص الحساب
          </span>
          <h1 className="text-3xl font-extrabold mt-3 text-slate-900">
            ما هي المواد الدراسية التي تدرسها؟
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            اختر موادك الحالية أو أضف مواد جديدة لكي يقوم مساعد مخمخ الذكي بتخصيص المحتوى والملخصات خصيصاً لك.
          </p>
        </div>

        {/* نموذج إضافة مادة جديدة */}
        <form onSubmit={handleAddCustomSubject} className="mb-6 flex gap-2">
          <input
            type="text"
            value={customSubject}
            onChange={(e) => setCustomSubject(e.target.value)}
            placeholder="أضف مادة دراسية أخرى غير موجودة بالقائمة..."
            className="flex-1 bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 placeholder:text-slate-400 shadow-sm"
          />
          <button
            type="submit"
            className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition cursor-pointer"
          >
            إضافة
          </button>
        </form>

        {/* قائمة المواد */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 mb-8 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">اختر موادك الدراسية:</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {availableSubjects.map((subject, index) => {
              const isSelected = selectedSubjects.includes(subject);
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => toggleSubject(subject)}
                  className={`text-right px-4 py-3 rounded-xl text-sm font-medium transition flex items-center justify-between border cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-50 border-indigo-600 text-indigo-900 shadow-sm'
                      : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <span>{subject}</span>
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${isSelected ? 'bg-indigo-600 text-white' : 'border border-slate-300'}`}>
                    {isSelected ? '✓' : ''}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* زر الحفظ والمتابعة */}
        <div className="flex items-center justify-between">
          <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-800 transition">
            تخطي هذه الخطوة مؤقتاً
          </Link>
          <Link
            href="/dashboard"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl text-sm font-medium transition shadow-lg shadow-indigo-600/20 inline-block text-center"
          >
            حفظ ومتابعة إلى لوحة التحكم
          </Link>
        </div>
      </div>
    </div>
  );
}