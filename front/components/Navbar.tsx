import Link from 'next/link';

export default function Navbar() {
  return (
    <header className="w-full border-b border-slate-800 bg-slate-900/50 backdrop-blur-md px-6 py-4 flex items-center justify-between text-white">
      <div className="flex items-center gap-2">
        <span className="bg-indigo-600 text-sm px-2.5 py-1 rounded-md font-bold tracking-wide">
          مخمخ
        </span>
        <span className="text-lg font-semibold tracking-tight">Makhmakh AI</span>
      </div>

      <nav className="hidden md:flex items-center gap-6 text-sm text-slate-300">
        <Link href="/" className="hover:text-indigo-400 transition">الرئيسية</Link>
        <Link href="/dashboard" className="hover:text-indigo-400 transition">لوحة التحكم</Link>
        <Link href="/chat" className="hover:text-indigo-400 transition">المساعد الذكي</Link>
        <Link href="/upload" className="hover:text-indigo-400 transition">رفع الملفات</Link>
      </nav>

      <div>
        <Link 
          href="/login" 
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-lg font-medium transition shadow-sm inline-block"
        >
          دخول
        </Link>
      </div>
    </header>
  );
}