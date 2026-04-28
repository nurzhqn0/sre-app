import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type AuthMode = 'login' | 'register'
type View = 'products' | 'orders' | 'chat' | 'status'

type User = {
  id: string
  username: string
  email: string
  role: string
  created_at: string
}

type Product = {
  id: string
  name: string
  description: string
  category: string
  inventory: number
  price: number
}

type Order = {
  id: string
  product_id: string
  product_name: string
  quantity: number
  unit_price: number
  total_price: number
  status: string
  created_at: string
}

type ChatMessage = {
  id: string
  room: string
  user_id: string
  username: string
  content: string
  created_at: string
}

type ServiceHealth = {
  service: string
  status: string
  detail?: string
}

const serviceEndpoints = [
  { key: 'auth-service', path: '/api/auth/health' },
  { key: 'user-service', path: '/api/users/health' },
  { key: 'product-service', path: '/api/products/health' },
  { key: 'order-service', path: '/api/orders/health' },
  { key: 'chat-service', path: '/api/chat/health' },
] as const

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  token?: string,
): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Content-Type', 'application/json')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(path, { ...init, headers })
  const isJson = response.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await response.json() : null

  if (!response.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String(payload.detail)
        : `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return payload as T
}

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('sre_token') ?? '')
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [activeView, setActiveView] = useState<View>('products')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [serviceHealth, setServiceHealth] = useState<ServiceHealth[]>([])
  const [statusMessage, setStatusMessage] = useState('Platform initialized. Register or log in to begin.')
  const [authForm, setAuthForm] = useState({
    username: '',
    email: '',
    password: '',
  })
  const [orderForm, setOrderForm] = useState({
    productId: '',
    quantity: 1,
  })
  const [room, setRoom] = useState('operations')
  const [chatDraft, setChatDraft] = useState('')
  const [chatConnection, setChatConnection] = useState('offline')
  const socketRef = useRef<WebSocket | null>(null)

  const loadProducts = async () => {
    try {
      const data = await requestJson<{ products: Product[] }>('/api/products/products')
      setProducts(data.products)
      setOrderForm((previous) => ({
        ...previous,
        productId: previous.productId || data.products[0]?.id || '',
      }))
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Unable to load products.')
    }
  }

  const loadHealth = async () => {
    const results = await Promise.all(
      serviceEndpoints.map(async (service) => {
        try {
          const response = await requestJson<ServiceHealth>(service.path)
          return response
        } catch (error) {
          return {
            service: service.key,
            status: 'degraded',
            detail: error instanceof Error ? error.message : 'Health check failed.',
          }
        }
      }),
    )
    setServiceHealth(results)
  }

  const loadProfile = async (accessToken: string) => {
    const user = await requestJson<User>('/api/users/me', undefined, accessToken)
    setCurrentUser(user)
  }

  const loadOrders = async (accessToken: string) => {
    const data = await requestJson<{ orders: Order[] }>('/api/orders/orders', undefined, accessToken)
    setOrders(data.orders)
  }

  const loadChatHistory = async (accessToken: string, activeRoom: string) => {
    const data = await requestJson<{ messages: ChatMessage[] }>(
      `/api/chat/rooms/${activeRoom}/messages`,
      undefined,
      accessToken,
    )
    setChatMessages(data.messages)
  }

  useEffect(() => {
    const bootstrapId = window.setTimeout(() => {
      void loadProducts()
      void loadHealth()
    }, 0)

    const intervalId = window.setInterval(() => {
      void loadHealth()
    }, 15000)

    return () => {
      window.clearTimeout(bootstrapId)
      window.clearInterval(intervalId)
    }
  }, [])

  useEffect(() => {
    if (token) {
      localStorage.setItem('sre_token', token)
      const syncId = window.setTimeout(() => {
        void loadProfile(token).catch((error: unknown) => {
          setCurrentUser(null)
          setStatusMessage(error instanceof Error ? error.message : 'Unable to load profile.')
        })
        void loadOrders(token).catch((error: unknown) => {
          setOrders([])
          setStatusMessage(error instanceof Error ? error.message : 'Unable to load orders.')
        })
        void loadChatHistory(token, room).catch((error: unknown) => {
          setChatMessages([])
          setStatusMessage(error instanceof Error ? error.message : 'Unable to load chat history.')
        })
      }, 0)

      return () => window.clearTimeout(syncId)
    }

    const resetId = window.setTimeout(() => {
      localStorage.removeItem('sre_token')
      setCurrentUser(null)
      setOrders([])
      setChatMessages([])
      setChatConnection('offline')
    }, 0)

    return () => {
      window.clearTimeout(resetId)
      return
    }
  }, [token, room])

  useEffect(() => {
    if (!token) {
      socketRef.current?.close()
      socketRef.current = null
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const websocket = new WebSocket(
      `${protocol}//${window.location.host}/ws/chat?token=${encodeURIComponent(token)}&room=${encodeURIComponent(room)}`,
    )
    socketRef.current = websocket

    websocket.onopen = () => {
      setChatConnection('live')
      setStatusMessage(`Connected to the ${room} room.`)
    }

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data) as ChatMessage
      setChatMessages((previous) => [...previous, message].slice(-50))
    }

    websocket.onclose = () => {
      setChatConnection('offline')
    }

    websocket.onerror = () => {
      setChatConnection('degraded')
      setStatusMessage('Chat connection degraded. Reconnect by refreshing or changing rooms.')
    }

    return () => {
      websocket.close()
    }
  }, [token, room])

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login'
    const payload =
      authMode === 'register'
        ? authForm
        : { username: authForm.username, password: authForm.password }

    try {
      const response = await requestJson<{ access_token: string; user: User }>(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setToken(response.access_token)
      setCurrentUser(response.user)
      setStatusMessage(
        authMode === 'register'
          ? `User ${response.user.username} registered successfully.`
          : `Welcome back, ${response.user.username}.`,
      )
      setAuthForm({ username: response.user.username, email: response.user.email, password: '' })
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Authentication failed.')
    }
  }

  const submitOrder = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) {
      setStatusMessage('Authentication is required before placing an order.')
      return
    }

    try {
      const createdOrder = await requestJson<Order>(
        '/api/orders/orders',
        {
          method: 'POST',
          body: JSON.stringify({
            product_id: orderForm.productId,
            quantity: Number(orderForm.quantity),
          }),
        },
        token,
      )

      setOrders((previous) => [createdOrder, ...previous])
      setStatusMessage(`Order ${createdOrder.id} created successfully.`)
      void loadHealth()
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Order creation failed.')
      void loadHealth()
    }
  }

  const sendMessage = () => {
    if (!chatDraft.trim() || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    socketRef.current.send(chatDraft.trim())
    setChatDraft('')
  }

  const handleLogout = () => {
    socketRef.current?.close()
    setToken('')
    setStatusMessage('Session cleared.')
  }

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="eyebrow">Containerized microservices with observability</div>
        <h1>Reliability control room for a Dockerized commerce platform.</h1>
        <p className="hero-copy">
          Authenticate users, browse products, create orders, exchange live chat messages, and
          monitor service health from one interface tuned for your assignment demo.
        </p>
        <div className="status-banner">{statusMessage}</div>
      </section>

      <section className="grid-layout">
        <aside className="control-panel">
          <div className="panel-header">
            <span>Access</span>
            <button type="button" className="ghost-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
          <form className="stack-form" onSubmit={submitAuth}>
            <div className="mode-switch">
              <button
                type="button"
                className={authMode === 'login' ? 'active' : ''}
                onClick={() => setAuthMode('login')}
              >
                Login
              </button>
              <button
                type="button"
                className={authMode === 'register' ? 'active' : ''}
                onClick={() => setAuthMode('register')}
              >
                Register
              </button>
            </div>

            <label>
              Username
              <input
                value={authForm.username}
                onChange={(event) =>
                  setAuthForm((previous) => ({ ...previous, username: event.target.value }))
                }
                placeholder="ops.lead"
                required
              />
            </label>

            {authMode === 'register' ? (
              <label>
                Email
                <input
                  type="email"
                  value={authForm.email}
                  onChange={(event) =>
                    setAuthForm((previous) => ({ ...previous, email: event.target.value }))
                  }
                  placeholder="ops@example.com"
                  required
                />
              </label>
            ) : null}

            <label>
              Password
              <input
                type="password"
                value={authForm.password}
                onChange={(event) =>
                  setAuthForm((previous) => ({ ...previous, password: event.target.value }))
                }
                placeholder="minimum 8 characters"
                required
              />
            </label>

            <button type="submit" className="primary-button">
              {authMode === 'register' ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <div className="user-card">
            <div className="panel-header">
              <span>User context</span>
              <span className={`pill ${currentUser ? 'online' : 'offline'}`}>
                {currentUser ? currentUser.role : 'guest'}
              </span>
            </div>
            {currentUser ? (
              <>
                <strong>{currentUser.username}</strong>
                <span>{currentUser.email}</span>
              </>
            ) : (
              <span>Sign in to unlock orders, profile data, and live chat.</span>
            )}
          </div>
        </aside>

        <section className="workspace">
          <nav className="workspace-nav">
            {(['products', 'orders', 'chat', 'status'] as View[]).map((view) => (
              <button
                key={view}
                type="button"
                className={activeView === view ? 'active' : ''}
                onClick={() => setActiveView(view)}
              >
                {view}
              </button>
            ))}
          </nav>

          {activeView === 'products' ? (
            <section className="workspace-panel">
              <div className="panel-header">
                <span>Product catalog</span>
                <button type="button" className="ghost-button" onClick={() => void loadProducts()}>
                  Refresh
                </button>
              </div>
              <div className="product-grid">
                {products.map((product) => (
                  <article key={product.id} className="product-card">
                    <div className="product-meta">
                      <span>{product.category}</span>
                      <span>{product.inventory} in stock</span>
                    </div>
                    <h2>{product.name}</h2>
                    <p>{product.description}</p>
                    <div className="product-footer">
                      <strong>${product.price.toFixed(2)}</strong>
                      <code>{product.id}</code>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}

          {activeView === 'orders' ? (
            <section className="workspace-panel">
              <div className="panel-header">
                <span>Order workflow</span>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => (token ? void loadOrders(token) : undefined)}
                >
                  Refresh
                </button>
              </div>

              <form className="order-form" onSubmit={submitOrder}>
                <label>
                  Product
                  <select
                    value={orderForm.productId}
                    onChange={(event) =>
                      setOrderForm((previous) => ({ ...previous, productId: event.target.value }))
                    }
                  >
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Quantity
                  <input
                    type="number"
                    min="1"
                    max="25"
                    value={orderForm.quantity}
                    onChange={(event) =>
                      setOrderForm((previous) => ({
                        ...previous,
                        quantity: Number(event.target.value),
                      }))
                    }
                  />
                </label>

                <button type="submit" className="primary-button">
                  Create order
                </button>
              </form>

              <div className="order-list">
                {orders.length === 0 ? (
                  <p className="empty-state">No orders yet. Create one after signing in.</p>
                ) : (
                  orders.map((order) => (
                    <article key={order.id} className="order-card">
                      <div>
                        <strong>{order.product_name}</strong>
                        <span>{new Date(order.created_at).toLocaleString()}</span>
                      </div>
                      <div>
                        <span>
                          {order.quantity} x ${order.unit_price.toFixed(2)}
                        </span>
                        <span className="pill online">{order.status}</span>
                      </div>
                      <div className="order-total">${order.total_price.toFixed(2)}</div>
                    </article>
                  ))
                )}
              </div>
            </section>
          ) : null}

          {activeView === 'chat' ? (
            <section className="workspace-panel">
              <div className="panel-header">
                <span>Realtime operations chat</span>
                <span className={`pill ${chatConnection === 'live' ? 'online' : 'offline'}`}>
                  {chatConnection}
                </span>
              </div>

              <div className="chat-toolbar">
                <label>
                  Room
                  <input value={room} onChange={(event) => setRoom(event.target.value)} />
                </label>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => (token ? void loadChatHistory(token, room) : undefined)}
                >
                  Load history
                </button>
              </div>

              <div className="chat-log">
                {chatMessages.map((message) => (
                  <article key={message.id} className="chat-message">
                    <div>
                      <strong>{message.username}</strong>
                      <span>{new Date(message.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p>{message.content}</p>
                  </article>
                ))}
              </div>

              <div className="chat-compose">
                <input
                  value={chatDraft}
                  onChange={(event) => setChatDraft(event.target.value)}
                  placeholder="Send a coordination update..."
                />
                <button type="button" className="primary-button" onClick={sendMessage}>
                  Send
                </button>
              </div>
            </section>
          ) : null}

          {activeView === 'status' ? (
            <section className="workspace-panel">
              <div className="panel-header">
                <span>Service health and evidence map</span>
                <button type="button" className="ghost-button" onClick={() => void loadHealth()}>
                  Refresh
                </button>
              </div>
              <div className="health-grid">
                {serviceHealth.map((service) => (
                  <article key={service.service} className="health-card">
                    <div className="panel-header">
                      <strong>{service.service}</strong>
                      <span className={`pill ${service.status === 'ok' ? 'online' : 'offline'}`}>
                        {service.status}
                      </span>
                    </div>
                    <p>{service.detail ?? 'Healthy and responding to probes.'}</p>
                  </article>
                ))}
              </div>
              <div className="evidence-card">
                <h2>Evidence checklist</h2>
                <p>Capture screenshots from the UI, Prometheus, Grafana, and the incident simulation commands.</p>
                <ul>
                  <li>Healthy platform state with products, orders, and chat</li>
                  <li>Prometheus targets page on port 9090</li>
                  <li>Grafana dashboard on port 3000</li>
                  <li>Degraded order-service during the incident override</li>
                  <li>Recovery after restoring the correct database configuration</li>
                </ul>
              </div>
            </section>
          ) : null}
        </section>
      </section>
    </main>
  )
}

export default App
