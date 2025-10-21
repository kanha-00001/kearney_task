import ChatComponent from './components/ChatComponent';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6">AI Chatbot MVP</h1>
      <ChatComponent />
    </div>
  );
}

export default App;