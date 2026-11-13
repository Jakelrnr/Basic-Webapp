
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "./components/DashboardLayout";
import Home from "./pages/Homepage";
import AccountPage from "./pages/Accountpage";
import LoginPage from "./pages/LoginPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import ProgressPage from "./pages/ProgressPage";
import SignUpPage from "./pages/SignUpPage";
import { Auth0Provider } from "@auth0/auth0-react";

export default function App() {
  return (
    <Auth0Provider
      domain={import.meta.env.VITE_AUTH0_DOMAIN}
      clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: "https://yourapp-api",
        scope: "openid profile email",
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* No sidebar */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/signup" element={<SignUpPage title="Register" />} />

          {/* With sidebar */}
          <Route element={<DashboardLayout />}>
            <Route path="/homepage" element={<Home />} />
            <Route path="/progress" element={<ProgressPage title="Progress" />} />
            <Route path="/settings" element={<PlaceholderPage title="Settings" />} />
            <Route path="/bookings" element={<PlaceholderPage title="Bookings" />} />
            <Route path="/support" element={<PlaceholderPage title="Support" />} />
            <Route path="/information" element={<PlaceholderPage title="Information" />} />
            <Route path="/profile" element={<PlaceholderPage title="Profile" />} />
            <Route path="/account" element={<AccountPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Auth0Provider>
  );
}
