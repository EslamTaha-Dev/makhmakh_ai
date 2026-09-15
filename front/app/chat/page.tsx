'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';

interface Message {
  id: number;
  sender: 'user' | 'ai';
  text: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, sender: 'ai', text: 'أهلاً بك! أنا مساعد مخمخ الذكي. كيف يمكنني مساعدتك في رحلتك التعليمية اليوم؟' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { id: Date.now(), sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // محاكاة رد ذكي تفعيلي من المنصة
    setTimeout(() => {
      const aiResponse: Message = {
        id: Date.now() + 1,
        sender: 'ai',
        text: `لقد تلقيت سؤالك بنجاح وقمت بتحليله عبر النظام: "${userMessage.text}". جارٍ تجهيز خريطة التعلم أو المصادر المرتبطة!`
      };
      setMessages((prev) => [...prev, aiResponse]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col justify-between">
        {/* صندوق المحادثة */}
        <div className="space-y-4 overflow-y-auto p-4 flex-1 mb-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-md px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-none'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-900 border border-slate-800 text-slate-400 px-4 py-3 rounded-2xl text-sm animate-pulse">
                مخمخ يفكر الآن... ⏳
              </div>
            </div>
          )}
        </div>

        {/* صندوق إدخال الرسالة (مفعل تماماً) */}
        <form onSubmit={handleSendMessage} className="flex gap-2 bg-slate-900 p-2 rounded-xl border border-slate-800">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="اكتب سؤالك أو استفسارك هنا..."
            className="flex-1 bg-transparent px-4 py-2 text-sm text-white focus:outline-none placeholder:text-slate-500"
          />
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition cursor-pointer shadow-md"
          >
            إرسال
          </button>
        </form>
      </div>
    </div>
  );
}