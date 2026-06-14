import { File, Paths } from 'expo-file-system';

function getFile(): File {
  return new File(Paths.document, '.appstore.json');
}

async function readStore(): Promise<Record<string, string>> {
  try {
    const f = getFile();
    if (!f.exists) return {};
    return JSON.parse(await f.text()) as Record<string, string>;
  } catch {
    return {};
  }
}

function writeStore(data: Record<string, string>): void {
  try {
    getFile().write(JSON.stringify(data));
  } catch {
    // Non-fatal
  }
}

export async function setItem<T>(key: string, value: T): Promise<void> {
  try {
    const store = await readStore();
    store[key] = JSON.stringify(value);
    writeStore(store);
  } catch {
    // Non-fatal
  }
}

export async function getItem<T>(key: string): Promise<T | null> {
  try {
    const store = await readStore();
    const raw = store[key];
    if (raw === undefined) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export async function removeItem(key: string): Promise<void> {
  try {
    const store = await readStore();
    delete store[key];
    writeStore(store);
  } catch {
    // Non-fatal
  }
}
