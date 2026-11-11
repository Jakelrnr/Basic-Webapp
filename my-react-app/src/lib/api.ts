import type {LoginCredentials} from "../types";

const USE_MOCK = false;
const API_URL = "http://localhost:8001";
export async function login(credentials: LoginCredentials): Promise<void> {
    if (USE_MOCK) {
        if (credentials.password !== "Admin0801") throw new Error("Invalid credentials");
        return;
    }

    const res = await fetch("http://localhost:8001/api/login", {
        method: "POST",
        credentials:"include",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(credentials),
    })
    if (!res.ok) throw new Error("Invalid credentials");}
    

export async function getMe(): Promise<{ id: number; username: string; role: string }> {
        const res = await fetch(`${API_URL}/api/me`, { credentials: "include" });
        if (!res.ok) throw new Error("Not logged in");
        return res.json();
    }
    
export async function logout(): Promise<void> {
        await fetch(`${API_URL}/api/logout`, { method: "POST", credentials: "include" });
    }

    export type Kpi = {
        total_kg: number;
        change_pct: number | null;
        area: string | null;
        area_avg_kg: number;
        rank: number | null;
        area_size: number;
        leaderboard: { rank: number; name: string; kg: number; you: boolean }[];
        trend: { month: string; kg: number }[];
      };
      
      export async function getKpi(): Promise<Kpi> {
        const res = await fetch(`${API_URL}/api/kpi`, { credentials: "include" });
        if (!res.ok) throw new Error("Couldn't load KPIs");
        return res.json();
      }