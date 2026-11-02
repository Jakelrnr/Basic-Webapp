import type {LoginCredentials} from "../types";

const USE_MOCK = true;
export async function login(credentials: LoginCredentials): Promise<{void}> {
    if (USE_MOCK) {
        if (creds.password !== "Admin0801") throw new Error("Invalid credentials");
        return
    }

    const res = await fetch("/api/login", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(creds),
    })
    if (!res.ok) throw new Error("Invalid credentials");}
    

