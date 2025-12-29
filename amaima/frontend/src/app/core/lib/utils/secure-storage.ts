import CryptoJS from 'crypto-js';

class SecureStorage {
  private encryptionKey: string;

  constructor() {
    this.encryptionKey = this.getOrCreateKey();
  }

  private getOrCreateKey(): string {
    if (typeof window === 'undefined') return '';
    
    const stored = localStorage.getItem('_ek');
    if (stored) return stored;

    const newKey = CryptoJS.lib.WordArray.random(32).toString();
    localStorage.setItem('_ek', newKey);
    return newKey;
  }

  setItem(key: string, value: any): void {
    if (typeof window === 'undefined') return;
    
    try {
      const stringValue = JSON.stringify(value);
      const encrypted = CryptoJS.AES.encrypt(stringValue, this.encryptionKey).toString();
      localStorage.setItem(`sec_${key}`, encrypted);
    } catch (error) {
      console.error('Failed to encrypt and store data:', error);
    }
  }

  getItem<T>(key: string): T | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const encrypted = localStorage.getItem(`sec_${key}`);
      if (!encrypted) return null;

      const decrypted = CryptoJS.AES.decrypt(encrypted, this.encryptionKey).toString(
        CryptoJS.enc.Utf8
      );
      return JSON.parse(decrypted) as T;
    } catch (error) {
      console.error('Failed to decrypt data:', error);
      return null;
    }
  }

  removeItem(key: string): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(`sec_${key}`);
  }

  clear(): void {
    if (typeof window === 'undefined') return;
    
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('sec_')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));
  }

  hasItem(key: string): boolean {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(`sec_${key}`) !== null;
  }
}

export const secureStorage = new SecureStorage();
