class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await response.text())
  }

  return response.json()
}

export function useApi() {
  return {
    get: <T>(url: string) => request<T>(url),
    post: <T>(url: string, body?: unknown) =>
      request<T>(url, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
    put: <T>(url: string, body?: unknown) =>
      request<T>(url, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
    patch: <T>(url: string, body?: unknown) =>
      request<T>(url, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
    delete: <T>(url: string) => request<T>(url, { method: 'DELETE' }),
  }
}
