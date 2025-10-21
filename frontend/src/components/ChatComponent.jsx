import { useState } from 'react';
     import axios from 'axios';
     import { Button } from './ui/button';
     import { Input } from './ui/input';
     import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

     function ChatComponent() {
       const [query, setQuery] = useState('');
       const [response, setResponse] = useState('');
       const [loading, setLoading] = useState(false);

       const handleQuery = async () => {
         if (!query) return;
         setLoading(true);
         try {
           const res = await axios.post('http://localhost:5000/query', { query });
           setResponse(res.data.response);
         } catch (err) {
           setResponse(err.response?.data?.error || 'Query failed');
         }
         setLoading(false);
       };

       return (
         <Card className="w-full max-w-md mt-4">
           <CardHeader>
             <CardTitle>Chat with Data</CardTitle>
           </CardHeader>
           <CardContent>
             <Input
               type="text"
               value={query}
               onChange={(e) => setQuery(e.target.value)}
               placeholder="Ask about the data..."
               className="mb-4"
             />
             <Button onClick={handleQuery} disabled={loading} className="w-full">
               {loading ? 'Processing...' : 'Send Query'}
             </Button>
             {response && (
               <div className="mt-4 p-4 bg-gray-100 rounded">
                 <p className="text-sm">{response}</p>
               </div>
             )}
           </CardContent>
         </Card>
       );
     }

     export default ChatComponent;