import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8080/api';

function App() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [activeTab, setActiveTab] = useState('orders');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrders();
    fetchProducts();
    fetchCustomers();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/orders`);
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      setError('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await fetch(`${API_BASE}/products`);
      const data = await res.json();
      setProducts(data);
    } catch (err) {
      setError('Failed to fetch products');
    }
  };

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API_BASE}/customers`);
      const data = await res.json();
      setCustomers(data);
    } catch (err) {
      setError('Failed to fetch customers');
    }
  };

  const deleteOrder = async (id) => {
    await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE' });
    fetchOrders();
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
      <h1>LegacyRetailManager</h1>
      <p>Legacy Java EE retail order management system with Spring Boot, JSF, EJB, MySQL, Kafka messaging, and a React frontend. Target migration to modern microservices.</p>

      <nav style={{ marginBottom: '20px' }}>
        <button onClick={() => setActiveTab('orders')} disabled={activeTab === 'orders'}>Orders</button>
        <button onClick={() => setActiveTab('products')} disabled={activeTab === 'products'}>Products</button>
        <button onClick={() => setActiveTab('customers')} disabled={activeTab === 'customers'}>Customers</button>
      </nav>

      {error && <div style={{ color: 'red' }}>{error}</div>}
      {loading && <div>Loading...</div>}

      {activeTab === 'orders' && (
        <OrdersTab orders={orders} onDelete={deleteOrder} onRefresh={fetchOrders} />
      )}
      {activeTab === 'products' && (
        <ProductsTab products={products} onRefresh={fetchProducts} />
      )}
      {activeTab === 'customers' && (
        <CustomersTab customers={customers} onRefresh={fetchCustomers} />
      )}
    </div>
  );
}

function OrdersTab({ orders, onDelete, onRefresh }) {
  const [form, setForm] = useState({ customerId: '', totalAmount: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customerId: Number(form.customerId), totalAmount: Number(form.totalAmount) }),
    });
    onRefresh();
  };

  return (
    <div>
      <h2>Orders</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Customer ID" value={form.customerId}
          onChange={e => setForm({ ...form, customerId: e.target.value })} />
        <input placeholder="Total Amount" value={form.totalAmount}
          onChange={e => setForm({ ...form, totalAmount: e.target.value })} />
        <button type="submit">Create Order</button>
      </form>
      <table border="1" cellPadding="8" style={{ marginTop: '10px', width: '100%' }}>
        <thead>
          <tr><th>ID</th><th>Customer ID</th><th>Status</th><th>Total</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {orders.map(order => (
            <tr key={order.id}>
              <td>{order.id}</td>
              <td>{order.customerId}</td>
              <td>{order.status}</td>
              <td>${order.totalAmount}</td>
              <td><button onClick={() => onDelete(order.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductsTab({ products, onRefresh }) {
  return (
    <div>
      <h2>Products</h2>
      <table border="1" cellPadding="8" style={{ width: '100%' }}>
        <thead>
          <tr><th>ID</th><th>Name</th><th>SKU</th><th>Price</th><th>Stock</th></tr>
        </thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.name}</td>
              <td>{p.sku}</td>
              <td>${p.price}</td>
              <td>{p.stockQuantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CustomersTab({ customers, onRefresh }) {
  return (
    <div>
      <h2>Customers</h2>
      <table border="1" cellPadding="8" style={{ width: '100%' }}>
        <thead>
          <tr><th>ID</th><th>First Name</th><th>Last Name</th><th>Email</th><th>Phone</th></tr>
        </thead>
        <tbody>
          {customers.map(c => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.firstName}</td>
              <td>{c.lastName}</td>
              <td>{c.email}</td>
              <td>{c.phone}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
