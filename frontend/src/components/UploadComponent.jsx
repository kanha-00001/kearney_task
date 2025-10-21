import { useState } from 'react';
     import axios from 'axios';
     import { Button } from './ui/button';
     import { Input } from './ui/input';
     import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

     function UploadComponent({ onUploadSuccess }) {
       const [file, setFile] = useState(null);
       const [status, setStatus] = useState('');

       const handleFileChange = (e) => {
         setFile(e.target.files[0]);
         setStatus('');
       };

       const handleUpload = async () => {
         if (!file) {
           setStatus('Please select a file');
           return;
         }
         const formData = new FormData();
         formData.append('file', file);
         try {
           const res = await axios.post('http://localhost:5000/upload', formData, {
             headers: { 'Content-Type': 'multipart/form-data' },
           });
           setStatus(res.data.message);
           onUploadSuccess();
         } catch (err) {
           setStatus(err.response?.data?.error || 'Upload failed');
         }
       };

       return (
         <Card className="w-full max-w-md">
           <CardHeader>
             <CardTitle>Upload CSV</CardTitle>
           </CardHeader>
           <CardContent>
             <Input
               type="file"
               accept=".csv"
               onChange={handleFileChange}
               className="mb-4"
             />
             <Button onClick={handleUpload} className="w-full">
               Upload
             </Button>
             {status && <p className="mt-2 text-sm text-gray-600">{status}</p>}
           </CardContent>
         </Card>
       );
     }

     export default UploadComponent;