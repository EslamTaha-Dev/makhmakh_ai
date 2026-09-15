'use client';

import { useState } from 'react';
import Link from 'next/link';
import Navbar from "@/components/Navbar";

// قائمة الأسئلة الشائعة
const faqs = [
  {
    question: "ما هي منصة مخمخ (Makhmakh AI)؟",
    answer: "هي منصة تعليمية ذكية تعتمد على تقنيات الذكاء الاصطناعي لمساعدة الطلاب في تلخيص المحاضرات، الإجابة على الأسئلة الدراسية، والتفاعل مع المستندات التعليمية لتحسين تجربة التعلم."
  },
  {
    question: "كيف يمكنني البدء في استخدام الموقع؟",
    answer: "يمكنك إنشاء حساب جديد مجاناً عبر صفحة التسجيل، ثم الانتقال لرفع ملفاتك الدراسية أو استخدام المساعد الذكي مباشرة لبدء طرح الأسئلة."
  },
  {
    question: "ما هي صيغ الملفات المدعومة للرفع؟",
    answer: "تدعم المنصة رفع المستندات الدراسية بصيغ متعددة مثل PDF، TXT، و DOCX لتتمكن من تحليلها واستخراج المعلومات منها بسهولة."
  },
  {
    question: "هل بياناتي ومستنداتي الشخصية آمنة؟",
    answer: "نعم، نولي اهتماماً كبيراً لخصوصية الطلاب وأمان بياناتهم، ولا يتم مشاركة أي ملفات أو محادثات خاصة بك مع أي طرف خارجي."
  },
  {
    question: "كيف يعمل المساعد الذكي في المنصة؟",
    answer: "يعتمد المساعد على تقنيات معالجة اللغات الطبيعية المتقدمة ونظم استرجاع المعلومات (RAG) لقراءة ملفاتك وفهم محتواها بدقة، ليقدم لك إجابات دقيقة ومستندة لمراجعك."
  },
  {
    question: "هل توجد قيود على حجم الملفات المرفوعة؟",
    answer: "نعم، الحد الأقصى لحجم الملف الواحد هو 10 ميجابايت لضمان سرعة المعالجة والتحليل بواسطة النظام."
  },
  {
    question: "كيف يمكنني استعادة كلمة المرور إذا نسيتها؟",
    answer: "يمكنك الانتقال إلى صفحة تسجيل الدخول، الضغط على رابط 'نسيت كلمة المرور؟'، وإدخال بريدك الإلكتروني لتلقي تعليمات استعادة الحساب."
  },
  {
    question: "هل المنصة مجانية للاستخدام؟",
    answer: "توفر المنصة باقة أساسية مجانية تتيح للطلاب الاستفادة من الميزات الرئيسية للذكاء الاصطناعي ورفع المستندات."
  },
  {
    question: "هل يمكنني استخدام المنصة من الهاتف المحمول؟",
    answer: "نعم، واجهة المنصة مصممة بتصميم متجاوب (Responsive) تعمل بكفاءة عالية على الهواتف الذكية، الأجهزة اللوحية، وأجهزة الكمبيوتر."
  },
  {
    question: "كيف يمكنني التواصل مع الدعم الفني في حال واجهت مشكلة؟",
    answer: "يمكنك التواصل معنا عبر قنوات الدعم المتاحة في المنصة أو إرسال استفسارك عبر البريد الإلكتروني الخاص بفريق العمل لمساعدتك في أسرع وقت."
  }
];

export default function Home() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  // مصفوفة التعليقات تبدأ فارغة تماماً
  const [comments, setComments] = useState<{ name: string; text: string }[]>([]);
  const [newName, setNewName] = useState('');
  const [newText, setNewText] = useState('');

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  const handleAddComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim() && newText.trim()) {
      setComments([{ name: newName.trim(), text: newText.trim() }, ...comments]);
      setNewName('');
      setNewText('');
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col relative">
      <Navbar />

      {/* زر/أيقونة الإعدادات العائمة في زاوية الصفحة */}
      <div className="absolute top-20 left-6 sm:left-10 z-10">
        <Link
          href="/settings"
          className="bg-slate-100 hover:bg-slate-200 text-slate-700 p-3 rounded-full shadow-sm border border-slate-200 flex items-center justify-center transition cursor-pointer"
          title="الإعدادات"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        </Link>
      </div>

      {/* القسم الرئيسي */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center py-20">
        <div className="max-w-xl">
          <span className="bg-indigo-50 text-indigo-600 border border-indigo-200 text-xs px-3 py-1 rounded-full uppercase tracking-wider font-semibold">
            Makhmakh AI Platform
          </span>

          <h1 className="text-4xl font-extrabold mt-4 mb-3 text-slate-900">
            مرحباً بك في منصة مخمخ التعليمية
          </h1>

          <p className="text-slate-600 mb-8 leading-relaxed">
            منصتك الذكية لتنظيم رحلتك التعليمية، رفع الملفات، واستكشاف خرائط التعلم التفاعلية بسهولة وسرعة.
          </p>

          <div className="flex gap-4 justify-center">
            <Link 
              href="/chat"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-medium transition shadow-lg shadow-indigo-600/20 cursor-pointer"
            >
              ابدأ التعلم الآن
            </Link>
          </div>
        </div>
      </main>

      {/* قسم آراء الطلاب */}
      <section className="py-16 px-6 max-w-4xl mx-auto w-full border-t border-slate-200">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-slate-900">آراء الطلاب عن المنصة</h2>
          <p className="text-slate-600 text-sm mt-2">شارِكنا برأيك أو تجربتك مع منصة مخمخ</p>
        </div>

        <form onSubmit={handleAddComment} className="bg-slate-50 border border-slate-200 p-6 rounded-2xl mb-10 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">اكتب تعليقك:</h3>
          <div className="space-y-4">
            <input
              type="text"
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="اسمك الكريم..."
              className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm"
            />
            <textarea
              required
              rows={3}
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              placeholder="اكتب انطباعك أو رأيك عن الموقع..."
              className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm resize-none"
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition cursor-pointer shadow-sm"
            >
              إضافة التعليق
            </button>
          </div>
        </form>

        {comments.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {comments.map((comment, index) => (
              <div key={index} className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex flex-col justify-between">
                <p className="text-slate-600 text-sm leading-relaxed mb-4">"{comment.text}"</p>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold flex items-center justify-center text-xs">
                    {comment.name.charAt(0)}
                  </div>
                  <span className="font-semibold text-sm text-slate-800">{comment.name}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-slate-400 text-sm py-6">لا توجد تعليقات حتى الآن. كن أول من يشاركنا رأيه!</p>
        )}
      </section>

      {/* قسم الأسئلة الشائعة */}
      <section className="py-16 px-6 max-w-4xl mx-auto w-full bg-slate-50 border-t border-slate-200">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900">
            الأسئلة الشائعة
          </h2>
          <p className="text-slate-600 text-sm mt-2">إجابات على أبرز الأسئلة حول منصة مخمخ</p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div 
              key={index} 
              className="bg-white border border-slate-200 rounded-2xl overflow-hidden transition shadow-sm"
            >
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full text-right px-6 py-4 flex justify-between items-center font-medium text-sm sm:text-base text-slate-800 hover:text-indigo-600 transition cursor-pointer"
              >
                <span>{faq.question}</span>
                <span className="text-indigo-600 text-xl font-bold transition-transform duration-300">
                  {openIndex === index ? '−' : '+'}
                </span>
              </button>
              
              {openIndex === index && (
                <div className="px-6 pb-4 text-slate-600 text-sm border-t border-slate-100 pt-3 leading-relaxed">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}