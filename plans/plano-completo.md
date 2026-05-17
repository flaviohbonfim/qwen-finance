# Plano Completo — Finance Control

Documento de referência para reconstrução do projeto do zero, incorporando todas as decisões de
arquitetura, convenções adotadas e armadilhas encontradas durante o desenvolvimento original.

---

## 1. Visão Geral

Aplicação full-stack de controle financeiro pessoal com:

- Autenticação por JWT (registro e login)
- Contas bancárias (saldo atualizado automaticamente por transação)
- Categorias com ícone e cor personalizados
- Transações (receitas/despesas, paginadas, filtráveis por tipo / conta / categoria)
- Dashboard com resumo mensal, gráfico de barras dos últimos 6 meses e pizza de despesas por categoria
- Relatórios anuais (barras + linha de evolução de saldo + tabela mensal)
- Configurações: perfil do usuário, alteração de senha, sistema de temas
- Sistema de temas: 9 temas pré-definidos (Claro, Escuro, Dracula, Nord, Catppuccin, Tokyo Night,
  Rosé Pine, Monokai, Solarized) + cor de destaque personalizada
- Layout responsivo (sidebar desktop + overlay mobile)

---

## 2. Stack Tecnológica

### Backend
| Pacote | Versão | Papel |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | ^0.115 | Framework HTTP |
| Uvicorn (standard) | ^0.32 | ASGI server com reload |
| SQLAlchemy (asyncio) | ^2.0 | ORM async |
| Alembic | ^1.14 | Migrations |
| aiomysql | ^0.2 | Driver MySQL async |
| Pydantic v2 (email) | ^2.10 | Validação + serialização |
| pydantic-settings | ^2.6 | Configuração via .env |
| python-jose (cryptography) | ^3.3 | JWT |
| bcrypt | ^4.2 | Hash de senhas |
| python-multipart | ^0.0.12 | Form data |
| Poetry | — | Gerenciador de dependências |

### Frontend
| Pacote | Versão | Papel |
|---|---|---|
| Node.js | 20 (Alpine) | Runtime |
| Vite | ^6.0 | Bundler / dev server |
| React | ^18.3 | UI |
| TypeScript | ^5.7 | Tipagem |
| TailwindCSS | ^3.4 | Utilitários CSS |
| Zustand | ^5.0 | Estado global (auth + tema) |
| TanStack Query v5 | ^5.62 | Servidor de estado / cache |
| Axios | ^1.7 | HTTP client |
| React Router DOM | ^6.28 | Roteamento |
| React Hook Form | ^7.54 | Formulários |
| Recharts | ^2.13 | Gráficos |
| Lucide React | ^0.468 | Ícones |
| date-fns | ^4.1 | Formatação de datas |

### Infraestrutura
| Ferramenta | Uso |
|---|---|
| Docker Compose | Ambiente de desenvolvimento local |
| MySQL 8.0 | Banco de dados |
| GitHub Actions | CI/CD — build, test e release |
| GHCR | Registro de imagens Docker (ARM64) |
| Oracle Cloud ARM64 | Servidor de produção |

---

## 3. Estrutura de Diretórios

```
finance-control/
├── docker-compose.yml
├── plans/
│   └── plano-completo.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── deps.py
│       │   └── v1/
│       │       ├── api.py
│       │       └── endpoints/
│       │           ├── auth.py
│       │           ├── accounts.py
│       │           ├── categories.py
│       │           ├── transactions.py
│       │           └── reports.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   └── security.py
│       ├── models/
│       │   ├── user.py
│       │   ├── account.py
│       │   ├── category.py
│       │   └── transaction.py
│       └── schemas/
│           ├── user.py
│           ├── account.py
│           ├── category.py
│           ├── transaction.py
│           └── report.py
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── types/
        │   └── index.ts
        ├── services/
        │   └── api.ts
        ├── store/
        │   ├── auth.ts
        │   └── theme.ts
        ├── themes/
        │   └── index.ts
        ├── hooks/
        │   └── useApi.ts
        ├── components/
        │   ├── layout/
        │   │   ├── Layout.tsx
        │   │   └── Sidebar.tsx
        │   └── ui/
        │       ├── Button.tsx
        │       ├── Card.tsx
        │       ├── Input.tsx
        │       ├── Select.tsx
        │       ├── Modal.tsx
        │       └── Badge.tsx
        └── pages/
            ├── Login.tsx
            ├── Register.tsx
            ├── Dashboard.tsx
            ├── Accounts.tsx
            ├── Categories.tsx
            ├── Transactions.tsx
            ├── Reports.tsx
            └── Settings.tsx
```

---

## 4. Docker Compose (desenvolvimento local)

```yaml
# docker-compose.yml
services:
  db:
    image: mysql:8.0
    container_name: finance_db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: finance_control
      MYSQL_USER: finance_user
      MYSQL_PASSWORD: finance_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: finance_backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=mysql+aiomysql://finance_user:finance_password@db:3306/finance_control
      - SECRET_KEY=change-this-secret-key-in-production
      - CORS_ORIGINS=http://localhost:5173,http://localhost:3000
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    image: node:20-alpine          # ⚠️ NÃO usar o Dockerfile de prod em dev
    container_name: finance_frontend
    restart: unless-stopped
    working_dir: /app
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://backend:8000   # ⚠️ Nome do serviço Docker, não localhost
    volumes:
      - ./frontend:/app
      - /app/node_modules            # volume anônimo para isolar node_modules do host
    command: sh -c "npm install && npm run dev -- --host"

volumes:
  mysql_data:
```

> **Armadilha:** O frontend usa `image: node:20-alpine` em vez de seu próprio Dockerfile.
> O Dockerfile de produção roda `npm ci` que exige `package-lock.json`. Em dev, sem o lock file
> gerado localmente, o comando falha. A solução é usar a imagem base e rodar `npm install`.

> **Armadilha:** `VITE_API_URL` deve apontar para o nome do serviço Docker (`backend`), não para
> `localhost`. Dentro de um container, `localhost` refere-se ao próprio container — o backend está
> em outro. O Vite proxy repassa `/api` para `http://backend:8000`.

---

## 5. Backend

### 5.1 pyproject.toml

```toml
[tool.poetry]
name = "finance-control-api"
version = "0.1.0"
description = "Personal Finance Control API"
authors = ["Autor <autor@email.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.36"}
alembic = "^1.14.0"
aiomysql = "^0.2.0"
pydantic = {extras = ["email"], version = "^2.10.0"}
pydantic-settings = "^2.6.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
bcrypt = "^4.2.0"
python-multipart = "^0.0.12"
httpx = "^0.28.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
ruff = "^0.8.0"
mypy = "^1.13.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 5.2 Configuração (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "mysql+aiomysql://finance_user:finance_password@localhost:3306/finance_control"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 dias
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

settings = Settings()
```

### 5.3 Database (`app/core/database.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 5.4 Segurança (`app/core/security.py`)

```python
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from app.core.config import settings

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(subject), "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

> **Armadilha crítica:** NÃO use `passlib` com `bcrypt >= 4.x`. O passlib internamente usa uma API
> do bcrypt que foi removida na versão 4, gerando `ValueError: password cannot be longer than 72 bytes`
> mesmo para senhas curtas. Use o pacote `bcrypt` diretamente conforme acima — `bcrypt = "^4.2.0"`.

### 5.5 Modelos SQLAlchemy

**User** — cascade delete em todas as relações:
```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete")
```

**Account** — `balance: Numeric(15,2)`, atualizado pelo endpoint de transações:
```python
class Account(Base):
    __tablename__ = "accounts"
    id / user_id / name / type(Enum) / balance: Numeric(15,2) / color: String(7) / created_at
```

**Category** — `icon: String(50)` armazena a chave string do ícone (ex: `"shopping-cart"`):
```python
class Category(Base):
    __tablename__ = "categories"
    id / user_id / name / type(Enum: income|expense) / icon: String(50) / color: String(7) / created_at
```

**Transaction** — `category_id` nullable (sem categoria é válido):
```python
class Transaction(Base):
    __tablename__ = "transactions"
    id / user_id / account_id / category_id(nullable) / type(Enum) / amount: Numeric(15,2)
    description: String(255) / notes: Text(nullable) / transaction_date: Date / created_at
```

### 5.6 Schemas Pydantic

> **Atenção Pydantic v2:** campos `Decimal` são serializados como **string** por padrão via JSON.
> No frontend, sempre converter com `Number(value)` ao usar em gráficos e cálculos.

```python
# app/schemas/user.py
class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int; name: str; email: str; is_active: bool; created_at: datetime

class UserUpdate(BaseModel):
    name: str; email: EmailStr

class UserChangePassword(BaseModel):
    current_password: str; new_password: str

class Token(BaseModel):
    access_token: str; token_type: str = "bearer"; user: UserOut
```

### 5.7 Dependency — usuário autenticado (`app/api/deps.py`)

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    # decode JWT → busca User no banco → verifica is_active → retorna User
    # Lança HTTP 401 em qualquer falha
```

### 5.8 Endpoints de Autenticação (`/api/v1/auth`)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cria usuário, retorna Token |
| POST | `/auth/login` | Autentica, retorna Token |
| GET | `/auth/me` | Retorna usuário atual |
| PUT | `/auth/me` | Atualiza nome/email (valida e-mail duplicado) |
| PUT | `/auth/me/password` | Altera senha (verifica senha atual, mín. 6 chars, retorna 204) |

### 5.9 Endpoints de Recursos

Todos os endpoints exigem `get_current_user` via `Depends` e filtram por `user_id`.

**Accounts** (`/api/v1/accounts`) — GET / POST / PUT `/{id}` / DELETE `/{id}`

**Categories** (`/api/v1/categories`) — GET (filtrável por `?type=income|expense`) / POST / PUT `/{id}` / DELETE `/{id}`

**Transactions** (`/api/v1/transactions`):
- GET com query params: `account_id`, `category_id`, `type`, `date_from`, `date_to`, `page`, `page_size`
- Retorna `PaginatedTransactions { items, total, page, page_size, pages }`
- POST/PUT/DELETE — **atualiza `account.balance`** automaticamente:
  - Create: `balance += amount` (receita) ou `balance -= amount` (despesa)
  - Update: reverte efeito antigo, aplica novo
  - Delete: reverte o efeito da transação deletada

**Reports** (`/api/v1/reports`):
- GET `/dashboard` — resumo do mês atual + últimos 6 meses + despesas por categoria
- GET `/monthly?year=YYYY` — resumo mês a mês do ano (12 registros)

> **Armadilha crítica — relatório de despesas por categoria:**
> A query **deve** partir de `Transaction` com LEFT JOIN em `Category`, não o contrário.
> Se partir de `Category`, transações sem categoria (category_id = NULL) são excluídas do resultado,
> pois não existem na tabela de categorias.
>
> ```python
> # CORRETO
> select(...).select_from(Transaction).join(Category, Transaction.category_id == Category.id, isouter=True)
>
> # ERRADO — exclui transações sem categoria
> select(...).select_from(Category).join(Transaction, ...)
> ```

### 5.10 Migração Alembic

```bash
# Inicializar (uma vez)
alembic init alembic

# Criar migração manualmente (não usar autogenerate em produção sem revisão)
alembic revision --autogenerate -m "initial schema"

# Aplicar no container
docker compose exec backend alembic upgrade head
```

A migration `001_initial_schema.py` cria as 4 tabelas na ordem correta (users → accounts → categories → transactions) e o `downgrade` as remove na ordem inversa.

---

## 6. Frontend

### 6.1 Configuração Vite (`vite.config.ts`)

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },  // alias @/ para src/
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: { outDir: "dist", sourcemap: false },
});
```

> **Armadilha:** O alias `@/` exige `@types/node` nas devDependencies e o campo `paths` no
> `tsconfig.json`. Sem isso, o TypeScript aceita mas o Vite falha em runtime com
> `Failed to resolve import '@/store/auth'`.
>
> ```json
> // tsconfig.json — adicionar dentro de "compilerOptions":
> "baseUrl": ".",
> "paths": { "@/*": ["./src/*"] }
> ```
>
> ```json
> // tsconfig.node.json — adicionar nas devDependencies do package.json:
> // "@types/node": "^22.10.0"
> ```

### 6.2 TailwindCSS (`tailwind.config.js`)

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eef2ff", 100: "#e0e7ff", 200: "#c7d2fe", 300: "#a5b4fc",
          400: "#818cf8", 500: "#6366f1", 600: "#4f46e5", 700: "#4338ca",
          800: "#3730a3", 900: "#312e81",
        },
      },
    },
  },
  plugins: [],
};
```

### 6.3 Tipos TypeScript (`src/types/index.ts`)

Definir interfaces para: `User`, `AuthResponse`, `AccountType`, `Account`, `CategoryType`,
`Category`, `TransactionType`, `Transaction`, `PaginatedTransactions`, `MonthlySummary`,
`CategorySummary`, `DashboardSummary`.

> Todos os campos de valor monetário vêm do backend como `string` (Pydantic v2 serializa `Decimal`
> assim). Declarar como `number` nos tipos TypeScript e converter com `Number(value)` ao usar.

### 6.4 Axios API Service (`src/services/api.ts`)

```typescript
import axios from "axios";
import { useAuthStore } from "@/store/auth";

const api = axios.create({ baseURL: "/api/v1" });

// Injeta token em todas as requisições
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Logout automático em 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 6.5 Zustand — Auth Store (`src/store/auth.ts`)

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      updateUser: (user) => set({ user }),   // usado após editar perfil
      logout: () => set({ token: null, user: null }),
    }),
    { name: "finance-auth" }  // chave no localStorage
  )
);
```

### 6.6 Sistema de Temas

#### Arquitetura

O sistema de temas usa **CSS custom properties** + seletor `html[data-theme]` para sobrescrever
classes Tailwind globalmente, sem alterar nenhum componente individualmente.

**Fluxo:**
1. `src/themes/index.ts` — define 9 temas, cada um com 17 propriedades de cor
2. `src/store/theme.ts` — Zustand com persist; ao trocar tema, chama `applyVars()` que:
   - Define `document.documentElement.setAttribute("data-theme", theme.id)`
   - Seta 17 variáveis CSS (`--theme-bg`, `--theme-surface`, etc.) via `style.setProperty`
3. `src/index.css` — regras globais `html[data-theme] .bg-white { background-color: var(--theme-surface) !important; }` cobrem todas as classes Tailwind usadas
4. `src/App.tsx` — chama `applyTheme()` no `useEffect` inicial para restaurar o tema persistido

#### Temas disponíveis (ids)
`light`, `dark`, `dracula`, `nord`, `catppuccin`, `tokyo-night`, `rose-pine`, `monokai`, `solarized`

#### Interface `ThemeColors` (17 propriedades)
```typescript
interface ThemeColors {
  bg: string;         surface: string;   surface2: string;  border: string;
  text1: string;      text2: string;     text3: string;
  accent: string;     accentHover: string; accentLight: string; accentFg: string;
  income: string;     incomeLight: string;
  expense: string;    expenseLight: string;
  sidebar: string;    inputBg: string;
}
```

#### CSS (`src/index.css`) — estrutura das overrides
```css
/* Variáveis padrão (tema claro) */
:root { --theme-bg: #f9fafb; --theme-surface: #ffffff; /* ... */ }

/* Overrides globais — aplicados a QUALQUER tema */
html[data-theme] .bg-white        { background-color: var(--theme-surface)  !important; }
html[data-theme] .bg-gray-50      { background-color: var(--theme-bg)       !important; }
html[data-theme] .text-gray-900   { color: var(--theme-text1)               !important; }
html[data-theme] .border-gray-100 { border-color: var(--theme-border)       !important; }
html[data-theme] input, select, textarea { background-color: var(--theme-input-bg) !important; }
html[data-theme] .bg-primary-600  { background-color: var(--theme-accent)   !important; }
html[data-theme] .text-green-600  { color: var(--theme-income)              !important; }
html[data-theme] .text-red-500    { color: var(--theme-expense)             !important; }
html[data-theme] aside            { background-color: var(--theme-sidebar)  !important; }

/* Sombras mais fortes para temas escuros */
html[data-theme="dark"] .shadow-sm,
html[data-theme="dracula"] .shadow-sm /* ... */ { box-shadow: 0 1px 2px 0 rgba(0,0,0,0.4) !important; }
```

> **Atenção:** As páginas de Login e Register ficam fora do layout principal e portanto fora do
> `<aside>`. Elas usam `bg-gradient-to-br from-primary-50 to-indigo-100` que **não** é coberta
> pelas overrides. Solução: usar `style` inline com variáveis CSS:
>
> ```tsx
> // ✅ CORRETO — responde ao tema
> <div style={{ background: "linear-gradient(135deg, var(--theme-accent-light) 0%, var(--theme-bg) 100%)" }}>
>   <div style={{ backgroundColor: "var(--theme-surface)" }}>
>
> // ❌ ERRADO — sempre claro
> <div className="bg-gradient-to-br from-primary-50 to-indigo-100">
>   <div className="bg-white">
> ```

### 6.7 React Query Hooks (`src/hooks/useApi.ts`)

Organizar os hooks em grupos por domínio:

- **Auth:** `useLogin`, `useRegister`, `useUpdateProfile`, `useChangePassword`
- **Accounts:** `useAccounts`, `useCreateAccount`, `useUpdateAccount`, `useDeleteAccount`
- **Categories:** `useCategories(type?)`, `useCreateCategory`, `useUpdateCategory`, `useDeleteCategory`
- **Transactions:** `useTransactions(params)`, `useCreateTransaction`, `useUpdateTransaction`, `useDeleteTransaction`
- **Reports:** `useDashboard`, `useMonthlyReport(year?)`

Mutations de criação/edição/deleção de transações devem invalidar os query keys
`["transactions"]`, `["accounts"]` e `["dashboard"]`, pois o saldo das contas muda.

### 6.8 Componentes UI

Todos são `forwardRef` onde aplicável, aceitam `className` extra e usam classes Tailwind.

- **Button** — variantes: `primary | secondary | danger | ghost`; tamanhos: `sm | md | lg`; prop `loading` exibe spinner
- **Input** — prop `label` e `error` (mensagem vermelha abaixo); passa todas as props nativas via spread
- **Select** — mesmo padrão do Input
- **Card** — prop `padding?: boolean` (padrão `true`); `bg-white rounded-xl shadow-sm border`
- **Modal** — fecha com `Escape` e click no backdrop; animação de slide vindo de baixo no mobile
- **Badge** — recebe `color` (hex) e aplica background com 20% de opacidade

### 6.9 Layout Responsivo

**Desktop (md+):** sidebar fixa de 256px à esquerda + área de conteúdo com scroll.

**Mobile:** sidebar escondida; topbar com botão hamburger abre overlay (div preto 50% opacidade +
sidebar z-50 de 288px de largura que fecha ao clicar fora ou em qualquer link).

```tsx
// Layout.tsx — estrutura
<div className="flex h-screen overflow-hidden bg-gray-50">
  <aside className="hidden md:flex md:w-64">  {/* desktop */}
    <Sidebar />
  </aside>

  {sidebarOpen && (
    <div className="fixed inset-0 z-40 md:hidden">  {/* mobile overlay */}
      <div className="absolute inset-0 bg-black/50" onClick={close} />
      <aside className="relative z-50 w-72 h-full">
        <Sidebar onClose={close} />
      </aside>
    </div>
  )}

  <div className="flex-1 flex flex-col overflow-hidden">
    <header className="md:hidden ...">  {/* topbar mobile */}
      <button onClick={open}><Menu /></button>
    </header>
    <main className="flex-1 overflow-y-auto p-4 md:p-6">
      <Outlet />
    </main>
  </div>
</div>
```

### 6.10 Roteamento (`src/App.tsx`)

```tsx
// Restaura tema na montagem
useEffect(() => { applyTheme(); }, [applyTheme]);

// Estrutura de rotas
<BrowserRouter>
  <Routes>
    <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
    <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
    <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
      <Route index              element={<Dashboard />} />
      <Route path="transactions" element={<Transactions />} />
      <Route path="accounts"    element={<Accounts />} />
      <Route path="categories"  element={<Categories />} />
      <Route path="reports"     element={<Reports />} />
      <Route path="settings"    element={<Settings />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
</BrowserRouter>
```

### 6.11 Página Dashboard

- 4 `StatCard`s: Saldo Total, Receitas do Mês, Despesas do Mês, Saldo do Mês
- Gráfico de barras (`Recharts BarChart`) — últimos 6 meses, receitas vs despesas
- Gráfico de pizza (`Recharts PieChart`) — despesas por categoria no mês corrente
- Lista de 5 transações recentes

> **Armadilha — StatCard:** NÃO calcular a cor de fundo via `string.replace` (ex:
> `color.replace("text-","bg-").replace("600","100")`). Isso falha para variantes como
> `text-red-500` → `bg-red-500` (tom errado) ou `text-primary-600` → `bg-primary-600` (muito escuro).
> Usar um objeto explícito:
>
> ```typescript
> const bgStyle = {
>   backgroundColor: color === "text-primary-600" ? "#eef2ff"
>     : color === "text-green-600" ? "#dcfce7"
>     : "#fee2e2",
> };
> ```

> **Armadilha — PieChart valores:** Recharts recebe `dataKey` e espera `number`. Pydantic v2
> serializa `Decimal` como string. Converter no `.map()` antes de passar para o componente:
>
> ```tsx
> data={data.expense_by_category.map((e) => ({ ...e, total: Number(e.total) }))}
> ```

> **Armadilha — PieChart labels:** A prop `label` do `<Pie>` renderiza texto inline dentro do
> SVG e fica truncado/sobreposto em gráficos pequenos. Remover `label` e construir uma lista
> customizada abaixo do `<ResponsiveContainer>`.

### 6.12 Página Categorias — Seleção de Ícone

A categoria armazena o ícone como string (chave do `ICON_MAP`). O formulário deve usar `react-hook-form`
com `setValue("icon", key)` ao clicar no botão do ícone — **não** um `<Select>` HTML, pois Select
não renderiza ícones visuais.

```typescript
const ICON_MAP: Record<string, LucideIcon> = {
  "tag": Tag, "shopping-cart": ShoppingCart, "home": Home,
  "car": Car, "utensils": Utensils, "heart": Heart, // ...
};

// No form — grade de botões com ícones
{Object.entries(ICON_MAP).map(([key, Icon]) => (
  <button type="button" key={key} onClick={() => setValue("icon", key)}
    className={selectedIcon === key ? "ring-2 ring-primary-500" : ""}>
    <Icon size={20} />
  </button>
))}
```

> **Armadilha:** Se `Select` for removido dos imports mas ainda existir no JSX (ex: campo "Tipo"),
> o build silencia o erro e o formulário renderiza texto em vez do componente. Sempre manter os
> imports sincronizados.

### 6.13 Página Transações — Layout Responsivo

Usar layouts separados para mobile e desktop — **não** tentar adaptar um único grid:

```tsx
{/* Mobile — flex com ações na segunda linha */}
<div className="flex sm:hidden items-center gap-3 px-4 py-3">
  ...
</div>

{/* Desktop — grid de 12 colunas */}
<div className="hidden sm:grid grid-cols-12 gap-2 px-4 py-3">
  ...
</div>
```

> **Armadilha:** Grid de 12 colunas em telas pequenas comprime tudo em uma linha e empilha os
> elementos de forma ilegível. A separação por breakpoint (`sm:hidden` / `hidden sm:grid`) é mais
> limpa do que tentar adaptar o grid.

### 6.14 Página Settings — Estrutura

```
Settings
├── <ProfileSection />        — form: nome + email; PUT /auth/me; atualiza useAuthStore
├── <PasswordSection />       — form: senha atual + nova + confirmação; PUT /auth/me/password
├── Temas                     — grid de <ThemeCard> com preview visual
├── Cor de destaque           — color picker + 12 presets + botão resetar
└── Tema atual                — emoji + nome + dark/light
```

---

## 7. Tabela de Armadilhas Conhecidas

| # | Contexto | Problema | Solução |
|---|---|---|---|
| 1 | Docker dev | `npm ci` falha sem `package-lock.json` | Usar `image: node:20-alpine` + `npm install` |
| 2 | Docker dev | Frontend não alcança backend via `localhost` | `VITE_API_URL=http://backend:8000` (nome do serviço Docker) |
| 3 | Frontend build | Alias `@/` não resolve | Adicionar `resolve.alias` no `vite.config.ts` + `paths` no `tsconfig.json` + `@types/node` |
| 4 | Backend | `passlib` + `bcrypt >= 4.x` gera `ValueError` | Usar `bcrypt` direto: `bcrypt.checkpw` / `bcrypt.hashpw` |
| 5 | Pydantic v2 | Campos `Decimal` viram string no JSON | Converter com `Number(value)` no frontend ao usar em cálculos/gráficos |
| 6 | Dashboard | Pie chart vazio mesmo com despesas | Query partia de `Category` (exclui sem categoria); corrigir com `.select_from(Transaction).join(Category, isouter=True)` |
| 7 | Dashboard | Labels do pie chart truncados/sobrepostos | Remover prop `label` do `<Pie>` e construir lista customizada abaixo |
| 8 | Dashboard | Ícone do StatCard transborda fundo colorido | Não usar `string.replace` para calcular cor de fundo; usar objeto explícito por variante |
| 9 | Categorias | Ícone sempre mostra "Tag" ao criar/editar | `<Select>` removido dos imports mas ainda usado no JSX; restaurar import. Seleção de ícone via `setValue()`, não `<Select>` |
| 10 | Transações | Layout quebrado no mobile | Grid de 12 colunas é ilegível em telas pequenas; usar layouts separados com `sm:hidden` / `hidden sm:grid` |
| 11 | Login/Register | Fundo sempre claro independente do tema | Classes Tailwind hardcoded (`bg-gradient`, `bg-white`) não são cobertas pelas overrides CSS; usar `style` inline com `var(--theme-*)` |

---

## 8. CI/CD — GitHub Actions

### 8.1 Trigger e Semantic Versioning

```yaml
# .github/workflows/release.yml
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: google-github-actions/release-please-action@v4
        id: release
        with:
          release-type: simple
          token: ${{ secrets.GITHUB_TOKEN }}
```

Usa **Conventional Commits** para gerar versões automaticamente:
- `feat:` → minor bump
- `fix:` → patch bump
- `feat!:` ou `BREAKING CHANGE:` → major bump

### 8.2 Build e Push de Imagens Docker (ARM64)

```yaml
  build:
    needs: release
    if: steps.release.outputs.release_created
    runs-on: ubuntu-latest
    steps:
      - uses: docker/setup-qemu-action@v3      # emulação ARM64
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: ./backend
          platforms: linux/arm64
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ steps.release.outputs.tag_name }}
      # idem para frontend com nginx
```

---

## 9. Deploy — Oracle Cloud ARM64

### 9.1 Estratégia Pull-Based

O servidor **não recebe webhooks**. Em vez disso, um cron job (a cada 5 minutos) consulta a API do
GitHub para verificar se há nova release e faz pull quando necessário. Isso evita expor portas SSH
ou endpoints de webhook.

### 9.2 Script de deploy

```bash
#!/bin/bash
# /opt/finance-control/deploy.sh
set -e

REPO="owner/finance-control"
CURRENT=$(cat /opt/finance-control/current_version 2>/dev/null || echo "none")
LATEST=$(curl -sf "https://api.github.com/repos/$REPO/releases/latest" | jq -r '.tag_name')

if [ "$LATEST" = "$CURRENT" ]; then exit 0; fi

echo "Atualizando: $CURRENT → $LATEST"
cd /opt/finance-control

# Atualiza docker-compose.yml com a nova tag
sed -i "s|:v[0-9.]*|:$LATEST|g" docker-compose.prod.yml

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "$LATEST" > /opt/finance-control/current_version
echo "Deploy concluído: $LATEST"
```

### 9.3 Crontab

```cron
*/5 * * * * /opt/finance-control/deploy.sh >> /var/log/finance-deploy.log 2>&1
```

### 9.4 docker-compose.prod.yml

```yaml
services:
  backend:
    image: ghcr.io/owner/finance-control/backend:v1.0.0
    environment:
      - DATABASE_URL=mysql+aiomysql://...@db:3306/finance_control
      - SECRET_KEY=${SECRET_KEY}       # via .env no servidor
      - CORS_ORIGINS=https://seudominio.com 
    restart: unless-stopped

  frontend:
    image: ghcr.io/owner/finance-control/frontend:v1.0.0
    ports: ["80:80", "443:443"]
    restart: unless-stopped

  db:
    image: mysql:8.0
    volumes: [mysql_data:/var/lib/mysql]
    restart: unless-stopped

volumes:
  mysql_data:
```

---

## 10. Checklist de Inicialização Local

```bash
# 1. Clonar repositório
git clone https://github.com/usuario/finance-control.git 
cd finance-control

# 2. Subir containers (banco, backend, frontend)
docker compose up -d --build

# 3. Aguardar banco ficar healthy e rodar migrations
docker compose exec backend alembic upgrade head

# 4. Acessar
# Frontend: http://localhost:5173
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

---

## 11. Checklist Pré-Produção

- [ ] Trocar `SECRET_KEY` por valor forte e aleatório (`openssl rand -hex 32`)
- [ ] Trocar senhas do banco de dados
- [ ] Configurar HTTPS (Let's Encrypt / Nginx reverse proxy)
- [ ] Ajustar `CORS_ORIGINS` para o domínio de produção
- [ ] Adicionar secrets no repositório GitHub para CI/CD
- [ ] Verificar firewall Oracle Cloud (portas 80, 443 abertas; 8000 fechada)
- [ ] Configurar backup automático do volume MySQL
- [ ] Monitoramento básico (uptime check do `/health`)
