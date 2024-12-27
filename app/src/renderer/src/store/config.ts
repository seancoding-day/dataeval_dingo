import { DEFAULT_SIDEBAR_WIDTH } from '@/constant';
import { createPersistStore } from '@/utils/store';

// Add these type definitions
type LLMModel = {
    name: string;
    available: boolean;
    provider?: { id: string };
};

enum StoreKey {
    Config = 'config',
}

export const DEFAULT_CONFIG = {
    models: [],
    lastUpdate: Date.now(), // timestamp, to merge state
    sidebarWidth: DEFAULT_SIDEBAR_WIDTH,
    name: 'config',
    version: 3.9,

    // Initialize other properties
};

export type AppConfig = typeof DEFAULT_CONFIG;

export const useAppConfig = createPersistStore(
    { ...DEFAULT_CONFIG },
    (set, get) => ({
        reset(): void {
            set(() => ({ ...DEFAULT_CONFIG }));
        },

        mergeModels(newModels: LLMModel[]): void {},

        allModels(): void {},
    }),
    {
        name: StoreKey.Config,
        version: 3.9,
        migrate(persistedState, version) {
            const state = persistedState as AppConfig;

            if (version < 3.4) {
                state.version = 3.4;
            }

            if (version < 3.5) {
                state.version = 3.5;
            }

            return state as any;
        },
    }
);
