/**
 * API service for MCP Memory system
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://memory.usemindmirror.com';

export interface TokenGenerationRequest {
  email: string;
  user_name?: string;
}

export interface TokenGenerationResponse {
  token: string;
  user_id: string;
  url: string;
  memory_limit: number;
  memories_used: number;
}

export interface WaitlistRequest {
  email: string;
}

export interface WaitlistResponse {
  message: string;
  email: string;
}

export interface ApiError {
  detail: string;
}

class MemoryApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async generateToken(request: TokenGenerationRequest): Promise<TokenGenerationResponse> {
    const response = await fetch(`${this.baseUrl}/api/generate-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to generate token');
    }

    return response.json();
  }

  async joinWaitlist(request: WaitlistRequest): Promise<WaitlistResponse> {
    const response = await fetch(`${this.baseUrl}/api/join-waitlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Failed to join waitlist');
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }
}

export const memoryApi = new MemoryApiService();