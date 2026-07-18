import axios from 'axios';

const API_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const api = {
  // Health
  async getHealth() {
    const { data } = await client.get('/health/detailed');
    return data;
  },

  // Events
  async getEvents(params?: { limit?: number; type?: string }) {
    const { data } = await client.get('/api/v1/events', { params });
    return data;
  },

  async createEvent(event: any) {
    const { data } = await client.post('/api/v1/events', event);
    return data;
  },

  // Memory
  async getMemories(params?: { limit?: number; type?: string; min_importance?: number }) {
    const { data } = await client.get('/api/v1/memory', { params });
    return data;
  },

  async getMemory(id: string) {
    const { data } = await client.get(`/api/v1/memory/${id}`);
    return data;
  },

  async createMemory(memory: any) {
    const { data } = await client.post('/api/v1/memory', memory);
    return data;
  },

  async searchMemories(query: string, limit?: number) {
    const { data } = await client.post('/api/v1/memory/search', { query, limit: limit || 10 });
    return data;
  },

  // Identity
  async getIdentity() {
    const { data } = await client.get('/api/v1/identity');
    return data;
  },

  async createIdentityNode(node: any) {
    const { data } = await client.post('/api/v1/identity/nodes', node);
    return data;
  },

  async createIdentityEdge(edge: any) {
    const { data } = await client.post('/api/v1/identity/edges', edge);
    return data;
  },

  // AI
  async complete(prompt: string, options?: { provider?: string; temperature?: number }) {
    const { data } = await client.post('/api/v1/ai/complete', {
      prompt,
      ...options,
    });
    return data;
  },

  async embed(text: string) {
    const { data } = await client.post('/api/v1/ai/embed', { text });
    return data;
  },

  async testAI() {
    try {
      const result = await this.complete('Say "hello" in one word.');
      return result.text?.length > 0;
    } catch {
      return false;
    }
  },

  // Reflection
  async getReflectionQuestions() {
    // For now, return mock questions
    // In production, this would call the reflection API
    return {
      questions: [
        { question: 'What did you work on today?', category: 'daily_work' },
        { question: 'Any wins or breakthroughs?', category: 'achievements' },
        { question: 'What challenged you?', category: 'challenges' },
        { question: 'Did you learn anything new?', category: 'learning' },
        { question: 'Any ideas worth capturing?', category: 'ideas' },
      ],
    };
  },

  async submitReflection(data: { responses: any[] }) {
    // For now, save each response as an event
    for (const response of data.responses) {
      await this.createEvent({
        type: 'learning',
        source: 'reflection',
        content: `${response.question}\n\n${response.answer}`,
        title: response.question,
      });
    }
    return { success: true };
  },
};
