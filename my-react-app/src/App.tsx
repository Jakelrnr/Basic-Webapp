import {BrowserRouter, Routes, Route,Link} from 'react-router-dom';
import HomePage from './pages/Homepage';
import AccountPage from './pages/Accountpage';
import LoginPage from './pages/LoginPage';

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/login">Login</Link>
          {" | "}

        <Link to="/account">Account</Link>
          {" | "}

        <Link to="/homepage">Homepage</Link>
          {" | "}

      </nav>
      <Routes>
        <Route path = "login" element={<LoginPage/>}/>
        <Route path = "account" element = {<AccountPage/>}/>
        <Route path = "homepage" element = {<HomePage/>}/>
      </Routes>
    </BrowserRouter>
  );
}