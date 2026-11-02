import {BrowserRouter, Routes, Route,Link, Navigate} from 'react-router-dom';
import HomePage from './pages/Homepage';
import AccountPage from './pages/Accountpage';
import LoginPage from './pages/LoginPage';

export default function App() {
  return (
    <BrowserRouter>
      
      <Routes>
        <Route path = "login" element={<LoginPage/>}/>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path = "account" element = {<AccountPage/>}/>
        <Route path = "homepage" element = {<HomePage/>}/>
      </Routes>

      {import.meta.env.DEV && (
        <nav className="fixed bottom-3 right-3 z-50 flex gap-3 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-400">

          <Link to="/homepage" className="hover:text-zinc-100">
           
          </Link>
          <Link to="/login" className="hover:text-zinc-100">
            
          </Link>
          <Link to="/account" className="hover:text-zinc-100">
            
          </Link>
        </nav>
        )}
    </BrowserRouter>
  );
}