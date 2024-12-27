import { useEffect, useState } from 'react';

export function useWindowSize(): { width: number; height: number } {
    const [size, setSize] = useState({
        width: window.innerWidth,
        height: window.innerHeight,
    });

    useEffect(() => {
        const onResize = () => {
            setSize({
                width: window.innerWidth,
                height: window.innerHeight,
            });
        };

        window.addEventListener('resize', onResize);

        return () => {
            window.removeEventListener('resize', onResize);
        };
    }, []);

    return size;
}

export const MOBILE_MAX_WIDTH = 600;
export function useMobileScreen(): boolean {
    const { width } = useWindowSize();

    return width <= MOBILE_MAX_WIDTH;
}
