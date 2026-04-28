CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    inventory INTEGER NOT NULL DEFAULT 0,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id),
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    room TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO products (id, name, description, category, inventory, price)
VALUES
    ('prd-observability-kit', 'Observability Starter Kit', 'Prometheus and Grafana starter bundle for new platform teams.', 'Monitoring', 22, 129.00),
    ('prd-chaos-lab', 'Chaos Lab Sandbox', 'Practice environment for incident rehearsals and rollback drills.', 'Reliability', 14, 249.00),
    ('prd-release-pulse', 'Release Pulse Dashboard', 'Executive dashboard package for deployment frequency and change failure rate.', 'Analytics', 30, 89.00),
    ('prd-runtime-guard', 'Runtime Guard Pack', 'Baseline alert rules and service health monitors for production APIs.', 'Security', 18, 159.00)
ON CONFLICT (id) DO NOTHING;
