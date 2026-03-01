# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## 🛠️ Backend Setup Instructions

### Initial Database Setup

1. **Start all database services (recommended)**:
```bash
cd backend
docker compose up -d
```

2. **Check service status**:
```bash
docker compose ps
```

3. **Install backend dependencies**:
```bash
cd backend
pip install -r requirements.txt
pip install -r database_requirements.txt
```

4. **Run the backend**:
```bash
cd backend
python3 app.py
```

5. **Stop services when done**:
```bash
cd backend
docker compose down
```

### Frontend Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Run development server**:
```bash
npm run dev
```

3. **Access the website**:
Open `http://localhost:5173` in your browser. You will be redirected to the login page.

4. **Create an account**:
- Click "Get Started" to sign up
- Enter your company details and credentials
- Your user data will be stored in PostgreSQL

5. **View your profile**:
- After login, click on your company name in the header to access your profile
- Edit your company information, location, and contact details

### Notes
- **Authentication Required**: All pages except login/signup require authentication
- **Database Integration**: User data is stored in PostgreSQL with password hashing
- **Neo4j credentials**: `neo4j/password`
- **PostgreSQL**: Exposed on host port `5433` to avoid conflicts with local installations
- **Keep credentials** in `backend/.env` aligned with `backend/docker-compose.yml`

