// frontend/src/pages/api/tasks.js
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default async function handler(req, res) {
  const { method } = req;

  try {
    switch (method) {
      case 'GET':
        const getResponse = await axios.get(`${API_BASE_URL}/tasks/`);
        res.status(200).json(getResponse.data);
        break;
      
      case 'POST':
        const postResponse = await axios.post(`${API_BASE_URL}/tasks/`, req.body);
        res.status(200).json(postResponse.data);
        break;
      
      case 'PUT':
        const putResponse = await axios.put(`${API_BASE_URL}/tasks/${req.query.id}`, req.body);
        res.status(200).json(putResponse.data);
        break;
      
      case 'DELETE':
        const deleteResponse = await axios.delete(`${API_BASE_URL}/tasks/${req.query.id}`);
        res.status(200).json(deleteResponse.data);
        break;
      
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        res.status(405).end(`Method ${method} Not Allowed`);
    }
  } catch (error) {
    console.error('API Error:', error.message);
    res.status(error.response?.status || 500).json({ 
      error: error.message, 
      details: error.response?.data 
    });
  }
}