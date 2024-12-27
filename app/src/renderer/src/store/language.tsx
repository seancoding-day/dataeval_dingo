import { create } from 'zustand';
import { Language } from '@/constant';
import { LOCALE_STORAGE_KEY } from '@/constant/storage';
import en from '@/locale/en';
import zh from '@/locale/zh';
import { IntlProvider } from 'react-intl';
type LanguageType = (typeof Language)[keyof typeof Language];

type LanguageStore = {
    language: LanguageType;
    setLanguage: (language: LanguageType) => void;
    toggleLanguage: () => void;
};

const getInitialLanguage = (): LanguageType => {
    // Try to get language setting from localStorage
    const savedLanguage = localStorage.getItem(
        LOCALE_STORAGE_KEY
    ) as LanguageType;
    if (savedLanguage && Object.values(Language).includes(savedLanguage)) {
        return savedLanguage;
    }

    // If no valid language setting in localStorage, try to get browser language
    const browserLanguage = navigator.language.toLowerCase();
    if (browserLanguage.startsWith('zh')) {
        return Language.ZH_CN;
    } else if (browserLanguage.startsWith('en')) {
        return Language.EN_US;
    }

    // Default to Chinese
    return Language.ZH_CN;
};

export const useLanguageStore = create<LanguageStore>(set => ({
    language: getInitialLanguage(),
    setLanguage: language => {
        localStorage.setItem(LOCALE_STORAGE_KEY, language);
        set({ language });
    },
    toggleLanguage: () =>
        set(state => {
            const newLanguage =
                state.language === Language.ZH_CN
                    ? Language.EN_US
                    : Language.ZH_CN;
            localStorage.setItem(LOCALE_STORAGE_KEY, newLanguage);
            return { language: newLanguage };
        }),
}));

const messages = {
    [Language.EN_US]: {
        ...en,
    },
    [Language.ZH_CN]: {
        ...zh,
    },
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({
    children,
}) => {
    const { language } = useLanguageStore();

    return (
        <IntlProvider
            messages={messages['zh-CN'] as unknown as Record<string, string>}
            locale={language}
            defaultLocale="zh-CN"
        >
            {children}
        </IntlProvider>
    );
};
