export interface User {
  id: number
  username: string
  email: string
  age?: number
  co2eqkg?: number
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterInput extends LoginCredentials {
  email: string
}

export interface Kpicard {
  title: string
  value: number
  unit: string
}