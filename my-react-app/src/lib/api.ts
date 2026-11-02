import type {LoginCredentials} from "../types";

const USE_MOCK = false;
export async function login(credentials: LoginCredentials): Promise<void> {
    if (USE_MOCK) {
        if (credentials.password !== "Admin0801") throw new Error("Invalid credentials");
        return;
    }

    const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(credentials),
    })
    if (!res.ok) throw new Error("Invalid credentials");}
    

