import { File, Paths } from 'expo-file-system';

function getFile(): File {
  return new File(Paths.document, '.auth.json');
}

async function read(): Promise<Record<string, string>> {
  try {
    const f = getFile();
    if (!f.exists) return {};
    return JSON.parse(await f.text()) as Record<string, string>;
  } catch {
    return {};
  }
}

function persist(data: Record<string, string>): void {
  getFile().write(JSON.stringify(data));
}

export async function saveToken(token: string): Promise<void> {
  const store = await read();
  store['auth_token'] = token;
  persist(store);
}

export async function getToken(): Promise<string | null> {
  return (await read())['auth_token'] ?? null;
}

export async function deleteToken(): Promise<void> {
  const store = await read();
  delete store['auth_token'];
  persist(store);
}

export async function saveUserId(userId: string): Promise<void> {
  const store = await read();
  store['user_id'] = userId;
  persist(store);
}

export async function getUserId(): Promise<string | null> {
  return (await read())['user_id'] ?? null;
}
