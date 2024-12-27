export type Updater<T> = (updater: (value: T) => void) => void;

export type MessageRole = (typeof ROLES)[number];

export interface RequestMessage {
    role: MessageRole;
    content: string;
}

export type DalleSize = '1024x1024' | '1792x1024' | '1024x1792';
export type DalleQuality = 'standard' | 'hd';
export type DalleStyle = 'vivid' | 'natural';
