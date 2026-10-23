import { useEffect, useState } from "react";

type User = { id: number; username: string; email: string };

export default function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function loadUsers() {
    const res = await fetch("http://localhost:8001/users");
    setUsers(await res.json());
  }

  useEffect(() => { loadUsers(); }, []);   // runs once when the page loads

  async function addUser() {
    const res = await fetch("http://localhost:8001/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
      alert((await res.json()).detail);
      return;
    }
    loadUsers();   // refresh the list
  }

  return (
    <div>
      <input placeholder="username" onChange={e => setUsername(e.target.value)} />
      <input placeholder="email" onChange={e => setEmail(e.target.value)} />
      <input placeholder="password" type="password" onChange={e => setPassword(e.target.value)} />
      <button onClick={addUser}>Add user</button>
      <ul>
        {users.map(u => <li key={u.id}>{u.username} ({u.email})</li>)}
      </ul>
    </div>
  );
}