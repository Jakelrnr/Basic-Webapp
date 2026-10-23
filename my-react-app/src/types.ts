export interface User{ 
  id: number;
  username: string;
  email: string;
  password: string;
  age?: number;
  co2eqkg?: number;
}

export interface Kpicard {
  title: string;
  value: number;
  unit: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}
