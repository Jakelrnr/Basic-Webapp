
import { NavLink, Link, Outlet } from "react-router-dom";
const links = [
  
  { to: "/progress", label: "Progress" },
  { to: "/settings", label: "Settings" },
  { to: "/bookings", label: "Bookings" },
  { to: "/support", label: "Support" },
  { to: "/information", label: "Information" },
  { to: "/profile", label: "Profile" },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-emerald-500/10 text-emerald-400"
      : "text-[#B4A6AB] hover:bg-white/5 hover:text-white"
  }`;

export default function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-[#1E152A] text-[#B4A6AB]">
      <aside className="sticky top-0 flex h-screen w-64 flex-col overflow-y-auto border-r border-white/10 p-5">
       <Link to="/homepage" className="text-3xl font-bold text-emerald-500">
  Dashboard
</Link>

        <nav className="mt-10 flex flex-col gap-1">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to} className={linkClass}>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto">
          <NavLink to="/account" className={linkClass}>
            Account
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 p-10">
        <Outlet />
      </main>
    </div>
  );
}