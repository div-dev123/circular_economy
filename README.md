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

1. **Start Required Services** (using Docker):
```bash
# Neo4j
docker run -p 7474:7474 -p 7687:7687 --name neo4j-container -e NEO4J_AUTH=neo4j/neo4j neo4j

# MongoDB
docker run -p 27017:27017 --name mongodb-container mongo

# Redis
docker run -p 6379:6379 --name redis-container redis

# Cassandra
docker run -p 9042:9042 --name cassandra-container cassandra:latest

# PostgreSQL
docker run -p 5432:5432 --name postgresql-container -e POSTGRES_PASSWORD=password -e POSTGRES_DB=circular_economy postgres
```

2. **Change Neo4j Default Password** (Required for first-time setup):
```bash
cd backend
python setup_neo4j_password.py
```

3. **Install Backend Dependencies**:
```bash
cd backend
pip install -r requirements.txt
pip install -r database_requirements.txt
```

4. **Update Environment Variables**:
Edit the `.env` file in the backend directory with your database credentials.
