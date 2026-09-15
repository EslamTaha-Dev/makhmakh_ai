'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setSuccessMessage('');
    }
  };

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);

    // محاكاة عملية رفع الملف ومعالجته عبر النظام الذكي
    setTimeout(() => {
      setUploading(false);
      setSuccessMessage(`تم رفع الملف "${selectedFile.name}" بنجاح وجارٍ تحليل محتواه بواسطة النظام!`);
      setSelectedFile(null);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-2xl w-full mx-auto p-6 flex flex-col justify-center">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold mb-2">رفع الملفات والمحاضرات</h1>
            <p className="text-slate-400 text-sm">
              ارفع ملفات الـ PDF أو المستندات الدراسية ليقوم نظام مخمخ بتحليلها ومساعدتك فيها.
            </p>
          </div>

          <form onSubmit={handleUpload} className="space-y-6">
            <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500 transition rounded-xl p-8 text-center bg-slate-950/50 cursor-pointer relative">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.txt,.docx"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="space-y-2">
                <span className="text-indigo-400 font-semibold text-sm">اضغط هنا لاختيار ملف</span>
                <p className="text-slate-500 text-xs">PDF, TXT, DOCX (الحد الأقصى 10 ميجابايت)</p>
              </div>
            </div>

            {selectedFile && (
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 flex items-center justify-between text-sm">
                <span className="text-slate-300 truncate font-medium">📄 {selectedFile.name}</span>
                <span className="text-indigo-400 text-xs">جاهز للرفع</span>
              </div>
            )}

            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className={`w-full py-3 rounded-xl font-medium text-sm transition shadow-md ${
                !selectedFile || uploading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer shadow-indigo-600/20'
              }`}
            >
              {uploading ? 'جاري الرفع والتحليل... ⏳' : 'رفع الملف الآن'}
            </button>
          </form>

          {successMessage && (
            <div className="mt-4 p-4 bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 text-sm rounded-xl text-center">
              {successMessage}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}