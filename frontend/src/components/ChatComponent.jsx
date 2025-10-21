import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { SendHorizonal } from 'lucide-react';

const API_URL = 'http://localhost:5000'; // Adjust if deployed

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollContainerRef = useRef(null);

  // Smart scrolling
  useEffect(() => {
    if (scrollContainerRef.current) {
      const { scrollHeight, clientHeight, scrollTop } = scrollContainerRef.current;
      if (scrollHeight - scrollTop <= clientHeight + 200) {
        scrollContainerRef.current.scrollTo({ top: scrollHeight, behavior: 'smooth' });
      }
    }
  }, [messages, isLoading]);

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;
    setMessages(prev => [...prev, { sender: 'human', text: messageText }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, { query: messageText }, {
        withCredentials: true // For session cookies
      });
      setMessages(prev => [...prev, { sender: 'ai', text: response.data.response }]);
    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages(prev => [...prev, { sender: 'ai', text: "⚠️ Something went wrong. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLoading) return;
    sendMessage(input);
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gradient-to-br from-gray-50 to-slate-200 p-4">
      <Card className="w-full max-w-3xl h-[95vh] flex flex-col border border-slate-200 shadow-2xl rounded-2xl overflow-hidden">
        <CardHeader className="border-b bg-slate-50">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Avatar className="border-2 border-white shadow-md">
                <AvatarImage src="https://api.dicebear.com/8.x/bottts/svg?seed=AI" alt="AI Avatar" />
                <AvatarFallback>AI</AvatarFallback>
              </Avatar>
              <div>
                <span className="font-semibold text-slate-800">AI Data Assistant</span>
                <p className="text-sm font-normal text-slate-500">Online</p>
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
            {isLoading && messages.length === 0 && (
              <div className="flex items-start gap-3 animate-pulse">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="https://api.dicebear.com/8.x/bottts/svg?seed=AI" alt="AI Avatar" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <div className="rounded-xl px-4 py-2.5 bg-white border border-slate-200 text-slate-800 shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="dot animate-bounce"></div>
                    <span className="text-sm text-slate-500">Connecting...</span>
                  </div>
                </div>
              </div>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`flex items-start gap-3 ${msg.sender === 'human' ? 'justify-end' : ''}`}>
                {msg.sender === 'ai' && (
                  <Avatar className="w-8 h-8">
                    <AvatarImage src="https://api.dicebear.com/8.x/bottts/svg?seed=AI" alt="AI Avatar" />
                    <AvatarFallback>AI</AvatarFallback>
                  </Avatar>
                )}
                <div className={`rounded-xl px-4 py-2.5 max-w-[80%] whitespace-pre-wrap shadow-md ${msg.sender === 'human' ? 'bg-blue-600 text-white' : 'bg-white text-slate-800 border border-slate-200'}`}>
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              </div>
            ))}
            {isLoading && messages.length > 0 && (
              <div className="flex items-start gap-3 animate-pulse">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="https://api.dicebear.com/8.x/bottts/svg?seed=AI" alt="AI Avatar" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <div className="rounded-xl px-4 py-2.5 bg-white border border-slate-200 text-slate-800 shadow-md">
                  <div className="flex items-center space-x-1">
                    <span className="dot animate-bounce"></span>
                    <span className="dot animate-bounce delay-150"></span>
                    <span className="dot animate-bounce delay-300"></span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="border-t p-4 bg-slate-100">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about the data..."
                disabled={isLoading}
                className="bg-white border-slate-300 focus-visible:ring-blue-500 focus-visible:ring-2"
                autoComplete="off"
              />
              <Button type="submit" disabled={isLoading} className="bg-blue-600 hover:bg-blue-700 text-white" size="icon">
                <SendHorizonal size={20} />
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ChatComponent;