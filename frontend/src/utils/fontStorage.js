/**
 * IndexedDB wrapper for custom font storage
 * Stores user-uploaded .woff2 font files with their configuration
 */

const DB_NAME = 'CustomFontsDB';
const STORE_NAME = 'fonts';
const DB_VERSION = 1;
const MAX_RECOMMENDED_SIZE = 500 * 1024; // 500KB

/**
 * Initialize IndexedDB for font storage
 * @returns {Promise<IDBDatabase>}
 */
export const initFontDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create object store if it doesn't exist
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'name' });
      }
    };
  });
};

/**
 * Validate font data before saving
 * @param {Object} font - Font object to validate
 * @throws {Error} If validation fails
 */
const validateFont = (font) => {
  if (!font.name || typeof font.name !== 'string') {
    throw new Error('Font name is required and must be a string');
  }

  if (!font.data || !(font.data instanceof ArrayBuffer)) {
    throw new Error('Font data is required and must be an ArrayBuffer');
  }

  if (!font.size || !font.size.match(/^\d+px$/)) {
    throw new Error('Font size is required and must be in format "XXpx"');
  }

  if (
    typeof font.lineHeight !== 'number' ||
    font.lineHeight < 0.5 ||
    font.lineHeight > 3.0
  ) {
    throw new Error('Line height must be a number between 0.5 and 3.0');
  }

  // Check file size and warn if large
  const sizeInKB = font.data.byteLength / 1024;
  if (font.data.byteLength > MAX_RECOMMENDED_SIZE) {
    console.warn(
      `Font "${font.name}" is ${sizeInKB.toFixed(1)}KB, which may impact performance. Recommended max: 500KB`
    );
  }
};

/**
 * Save a custom font to IndexedDB
 * @param {Object} font - Font object with name, data (ArrayBuffer), size, lineHeight
 * @returns {Promise<boolean>}
 */
export const saveCustomFont = async (font) => {
  validateFont(font);

  const db = await initFontDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    const fontRecord = {
      name: font.name,
      data: font.data,
      size: font.size,
      lineHeight: font.lineHeight,
      uploadedAt: new Date().toISOString(),
    };

    const request = store.put(fontRecord);

    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Get all custom fonts from IndexedDB
 * @returns {Promise<Array>}
 */
export const getCustomFonts = async () => {
  const db = await initFontDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Get a specific custom font by name
 * @param {string} name - Font name
 * @returns {Promise<Object|null>}
 */
export const getCustomFont = async (name) => {
  const db = await initFontDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(name);

    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Delete a custom font from IndexedDB
 * @param {string} name - Font name
 * @returns {Promise<boolean>}
 */
export const deleteCustomFont = async (name) => {
  const db = await initFontDB();

  // Check if font exists first
  const existing = await getCustomFont(name);
  if (!existing) {
    return false;
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(name);

    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Convert ArrayBuffer to base64 data URL for @font-face
 * @param {ArrayBuffer} buffer - Font file data
 * @returns {string} - Data URL
 */
export const arrayBufferToDataURL = (buffer) => {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  return `data:font/woff2;base64,${base64}`;
};

/**
 * Generate @font-face CSS rule for a custom font
 * @param {Object} font - Font object with name and data
 * @returns {string} - CSS @font-face rule
 */
export const generateFontFaceCSS = (font) => {
  const dataURL = arrayBufferToDataURL(font.data);
  return `
    @font-face {
      font-family: '${font.name}';
      src: url('${dataURL}') format('woff2');
      font-display: swap;
    }
  `;
};
