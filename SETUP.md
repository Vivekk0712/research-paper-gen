# IEEE Paper Generator - Setup Guide

## Frontend-Backend Connection Setup

### 1. Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials:
   # - SUPABASE_URL=your_supabase_project_url
   # - SUPABASE_KEY=your_supabase_anon_key
   # - GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Set up database**:
   - Run the SQL commands in `schema.sql` in your Supabase database
   - Ensure pgvector extension is enabled

5. **Test setup**:
   ```bash
   python test_setup.py
   ```

6. **Start backend server**:
   ```bash
   python start.py
   ```
   Backend will run on: http://localhost:8000

### 2. Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Default values should work for local development
   ```

4. **Start frontend server**:
   ```bash
   npm run dev
   ```
   Frontend will run on: http://localhost:3000

### 3. Connection Configuration

#### Backend CORS Settings
The backend is configured to accept requests from:
- `http://localhost:3000` (Vite dev server)
- `http://localhost:5173` (Alternative Vite port)

#### Frontend Proxy Settings
Vite is configured to proxy API calls:
- `/api/*` requests are forwarded to `http://localhost:8000`

#### Environment Variables

**Backend (.env)**:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_api_key
```

**Frontend (.env)**:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=IEEE Paper Generator
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.docx
```

### 4. Testing the Connection

1. **Start both servers**:
   - Backend: `python backend/start.py`
   - Frontend: `npm run dev` (in frontend directory)

2. **Check connection status**:
   - Open http://localhost:3000
   - Look for connection status indicator in the header
   - Check browser console for connection test results

3. **Manual API testing**:
   - Visit http://localhost:8000/docs for API documentation
   - Test endpoints directly in the Swagger UI

### 5. Troubleshooting

#### Backend Issues
- **Port 8000 already in use**: Change port in `start.py` or kill existing process
- **Database connection failed**: Check Supabase credentials and network
- **Gemini API errors**: Verify API key and quota

#### Frontend Issues
- **Cannot connect to backend**: Ensure backend is running on port 8000
- **CORS errors**: Check backend CORS configuration
- **Environment variables not loading**: Ensure `.env` file exists and variables start with `VITE_`

#### Connection Issues
- **Proxy not working**: Check Vite proxy configuration in `vite.config.js`
- **API calls failing**: Check network tab in browser dev tools
- **Mixed content errors**: Ensure both frontend and backend use same protocol (http/https)

### 6. Production Deployment

For production deployment, update:

1. **Backend**:
   - Set production database URLs
   - Configure proper CORS origins
   - Use production-grade WSGI server

2. **Frontend**:
   - Update `VITE_API_BASE_URL` to production backend URL
   - Build for production: `npm run build`
   - Serve static files from `dist/` directory

### 7. API Endpoints

The backend provides these main endpoints:
- `POST /api/papers` - Create new paper
- `POST /api/papers/{id}/upload` - Upload reference files
- `POST /api/generate` - Generate paper sections
- `GET /api/papers/{id}/sections` - Get paper sections
- `GET /api/papers/{id}/export` - Export complete paper

All endpoints are documented at: http://localhost:8000/docs