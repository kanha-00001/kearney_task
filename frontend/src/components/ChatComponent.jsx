import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { SendHorizonal } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// --- Self-Contained UI Components ---
const Card = ({ className, children }) => <div className={`bg-white rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}>{children}</div>;
const CardHeader = ({ className, children }) => <div className={`flex flex-col space-y-1.5 p-6 ${className}`}>{children}</div>;
const CardTitle = ({ className, children }) => <h3 className={`text-2xl font-semibold leading-none tracking-tight ${className}`}>{children}</h3>;
const CardContent = ({ className, children }) => <div className={`p-6 pt-0 ${className}`}>{children}</div>;
const Input = ({ className, ...props }) => <input className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`} {...props} />;
const Button = ({ className, size, ...props }) => <button className={`inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${size === 'icon' ? 'h-10 w-10' : 'h-10 px-4 py-2'} ${className}`} {...props} />;
const Avatar = ({ className, children }) => <div className={`relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`}>{children}</div>;
const AvatarImage = ({ src, alt, className }) => <img src={src} alt={alt} className={`aspect-square h-full w-full ${className}`} />;
const AvatarFallback = ({ children, className }) => <span className={`flex h-full w-full items-center justify-center rounded-full bg-muted ${className}`}>{children}</span>;

function ChatComponent() {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: "Hello! I'm your AI Data Assistant. I'm ready to answer questions about the provided data. What would you like to know?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // MODIFICATION: Add state to hold the session ID
  const [sessionID, setSessionID] = useState(null);
  const scrollContainerRef = useRef(null);

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
      // MODIFICATION: Include session_id in the request payload
      const payload = { 
        query: messageText,
        session_id: sessionID // Will be null on the first request
      };

      const response = await axios.post(`${API_URL}/query`, payload);
      
      // MODIFICATION: Update the session ID from the server's response
      if (response.data.session_id) {
        setSessionID(response.data.session_id);
      }
      
      setMessages(prev => [...prev, { sender: 'ai', text: response.data.response }]);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage = error.response?.data?.error || "⚠️ Something went wrong. Please try again.";
      setMessages(prev => [...prev, { sender: 'ai', text: errorMessage }]);
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
    <>
      <style>{`
        .dot { width: 8px; height: 8px; background-color: #94a3b8; border-radius: 50%; }
        .delay-150 { animation-delay: 0.15s; }
        .delay-300 { animation-delay: 0.3s; }
      `}</style>
      <div className="flex justify-center items-center h-screen bg-gradient-to-br from-gray-50 to-slate-200 p-4">
        <Card className="w-full max-w-3xl h-full flex flex-col border border-slate-200 shadow-2xl rounded-2xl overflow-hidden">
          <CardHeader className="border-b bg-slate-50 p-4">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Avatar className="border-2 border-white shadow-md">
                  <AvatarImage src="https://api.dicebear.com/8.x/bottts/svg?seed=AI" alt="AI Avatar" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <div>
                  <span className="font-semibold text-slate-800 text-base">AI Data Assistant</span>
                  <p className="text-sm font-normal text-slate-500">Online</p>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50 min-h-0">
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
              {isLoading && (
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
                <Button type="submit" disabled={isLoading || !input.trim()} className="bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-400" size="icon">
                  <SendHorizonal size={20} />
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

export default ChatComponent;

