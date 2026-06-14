import { useEffect, useState } from "react";

function App() {
  const [users, setUsers] = useState([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");

  // Fetch users
  const loadUsers = () => {
    fetch("http://127.0.0.1:5000/api/users")
      .then((res) => res.json())
      .then((data) => setUsers(data.users));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  // Add user
  const addUser = (e) => {
    e.preventDefault();

    fetch("http://127.0.0.1:5000/api/add-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        password,
        role,
      }),
    })
      .then((res) => res.json())
      .then(() => {
        setUsername("");
        setPassword("");
        setRole("");
        loadUsers();
      });
  };

  return (
    <div style={{ width: "400px", margin: "50px auto" }}>
      <h2>Electra – Add User</h2>

      <form onSubmit={addUser}>
        <input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <br /><br />

        <input
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <br /><br />

        <input
          placeholder="Role (admin/user)"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
        />
        <br /><br />

        <button type="submit">Add User</button>
      </form>

      <hr />

      <h3>Users List</h3>
      <ul>
        {users.map((u, index) => (
          <li key={index}>
            {u[1]} — {u[3]}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
