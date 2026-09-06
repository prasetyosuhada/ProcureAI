import { apiBaseURL } from './client';
import { UserContext } from '../types/chat';
import { TransientActivity } from '../types/requests';

interface ActivityEvent {
  type: 'activity';
  run_id: string;
  activity: TransientActivity;
}

interface ResultEvent<T> {
  type: 'result';
  run_id: string;
  data: T;
}

interface ErrorEvent {
  type: 'error';
  run_id: string;
  detail: string;
}

type ProcurementStreamEvent<T> =
  | ActivityEvent
  | ResultEvent<T>
  | ErrorEvent;

export interface StreamRequestOptions {
  signal?: AbortSignal;
  onActivity: (activity: TransientActivity) => void;
}

function buildHeaders(userContext?: UserContext): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: 'text/event-stream',
    'Content-Type': 'application/json',
  };
  if (userContext) {
    headers['X-User-ID'] = userContext.userId;
    headers['X-User-Name'] = userContext.userName;
    headers['X-Department-ID'] = userContext.departmentId;
    headers['X-Cost-Center'] = userContext.costCenter;
  }
  return headers;
}

async function readHttpError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || `Request failed with HTTP ${response.status}`;
  } catch {
    return `Request failed with HTTP ${response.status}`;
  }
}

function parseFrame<T>(frame: string): ProcurementStreamEvent<T> | null {
  const data = frame
    .split(/\r?\n/)
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())
    .join('\n');
  if (!data) return null;
  return JSON.parse(data) as ProcurementStreamEvent<T>;
}

export async function streamPost<T>(
  path: string,
  body: unknown,
  userContext: UserContext | undefined,
  options: StreamRequestOptions
): Promise<T> {
  const response = await fetch(
    `${apiBaseURL.replace(/\/$/, '')}${path}`,
    {
      method: 'POST',
      headers: buildHeaders(userContext),
      body: JSON.stringify(body),
      signal: options.signal,
    }
  );

  if (!response.ok) {
    throw new Error(await readHttpError(response));
  }
  if (!response.body) {
    throw new Error('Streaming response body is unavailable');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result: T | undefined;

  const handleFrame = (frame: string) => {
    const event = parseFrame<T>(frame);
    if (!event) return;
    if (event.type === 'activity') {
      options.onActivity(event.activity);
    } else if (event.type === 'result') {
      result = event.data;
    } else if (event.type === 'error') {
      throw new Error(event.detail);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || '';
    for (const frame of frames) handleFrame(frame);

    if (done) break;
  }

  if (buffer.trim()) handleFrame(buffer);
  if (result === undefined) {
    throw new Error('Stream ended before returning a result');
  }
  return result;
}
