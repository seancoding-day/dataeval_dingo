module.exports = {
    theme: {
        colors: {
            // 用法: className="text-gray"
            'black-1': '#121316', // 默认全局字体颜色
            blue: '#0D53DE', // 默认全局蓝色
            red: '#F5483B', // 默认全局红色
            gray: '#F4F5F9',
            'gray-2': '#464A53',
        },
        screens: {
            '3xl': '1920px', // 常见4K显示器
            '4xl': '2560px', // 2K/QHD显示器
            '5xl': '3840px', // 4K/UHD显示器
        },
        extend: {
            colors: {},
            backgroundImage: {
                linearBlue:
                    "url('https://static.openxlab.org.cn/llm-bayesian/assets/imgs/linearBlue.png')", // 默认全局背景
                chemicalTransferBg:
                    'linear-gradient(180deg, rgba(92, 147, 255, 0.10) -13.23%, rgba(255, 255, 255, 0.00) 83.57%)',
            },
        },
    },
    content: [
        './src/renderer/index.html',
        './src/renderer/src/**/*.{js,jsx,ts,tsx,ejs}',
    ],
    plugins: [
        // 默认全局滚动条
        // 用法: className="scrollbar-thin"
        require('@tailwindcss/line-clamp'),
        function ({ addUtilities }) {
            const newUtilities = {
                '.scrollbar-thin': {
                    scrollbarWidth: '2px',
                    // scrollbarColor: 'rgba(13, 83, 222, 1)',
                    '&::-webkit-scrollbar': {
                        width: '6px',
                        height: '6px',
                    },
                    '&::-webkit-scrollbar-track': {
                        backgroundColor: 'transparent',
                    },
                    '&::-webkit-scrollbar-thumb': {
                        // backgroundColor: 'rgba(13, 83, 222, 0.01)',
                        borderRadius: '20px',
                        border: '3px solid transparent',
                    },
                    '&:hover::-webkit-scrollbar-thumb': {
                        width: '6px',
                        border: '3px solid rgb(229 231 235)',
                        backgroundColor: 'rgb(229 231 235)',
                    },
                },

                // 你可以添加更多自定义的滚动条样式
                '.side-width': {
                    width: 'var(--sidebar-width)',
                    minWidth: 'var(--sidebar-width)',
                },

                '.main-content-width': {
                    width: 'calc(100% - var(--sidebar-width))',
                },
            };
            addUtilities(newUtilities, ['responsive', 'hover']);
        },
    ],

    // ...other configurations
};
