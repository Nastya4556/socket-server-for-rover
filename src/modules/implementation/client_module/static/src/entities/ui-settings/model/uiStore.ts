import { makeAutoObservable } from 'mobx';

const STORAGE_THEME = 'artex_theme';

export type ThemeMode = 'light' | 'dark';

// TODO: переработать на 2 разных компонента
export class UiStore {
  themeMode: ThemeMode = 'dark';

  /** Показывать overlay перетаскивания файла */
  dragOverlayVisible = false;

  constructor() {
    makeAutoObservable(this);
    try {
      const saved = localStorage.getItem(STORAGE_THEME) as ThemeMode | null;
      if (saved === 'light' || saved === 'dark') this.themeMode = saved;
    } catch(e) {
      console.error(e);
    }
  }

  setThemeMode(mode: ThemeMode) {
    this.themeMode = mode;
    try {
      localStorage.setItem(STORAGE_THEME, mode);
    } catch {
      console.error('Failed to save theme mode to localStorage');
    }
  }

  toggleTheme() {
    this.setThemeMode(this.themeMode === 'dark' ? 'light' : 'dark');
  }

  setDragOverlayVisible(visible: boolean) {
    this.dragOverlayVisible = visible;
  }
}

export const uiStore = new UiStore();
