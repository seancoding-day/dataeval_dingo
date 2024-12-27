import { resolve, join } from 'path';
import { defineConfig, externalizeDepsPlugin } from 'electron-vite';
import react from '@vitejs/plugin-react';
import fs from 'fs-extra';

const sharedConfig = {
    resolve: {
        alias: {
            '@': resolve('src/renderer/src/'),
            '@app': resolve('app'),
        },
    },
    css: {
        modules: {
            localsConvention: 'camelCaseOnly',
            scopeBehaviour: 'local',
            generateScopedName: '[name]__[local]___[hash:base64:5]',
        },
    },
    plugins: [react()],
};

export default defineConfig(({ command, mode }) => {
    if (mode === 'web') {
        return {
            main: {},
            preload: {},
            renderer: {
                ...sharedConfig,
                build: {
                    outDir: '../web-static',
                    emptyOutDir: true,
                    rollupOptions: {
                        input: {
                            main: resolve(
                                __dirname,
                                './src/renderer/index.html'
                            ),
                        },
                    },
                },
                server: {
                    hmr: true,
                },
                plugins: [
                    ...sharedConfig.plugins,
                    {
                        name: 'copy-iconfont',
                        writeBundle() {
                            const srcPath = join(
                                __dirname,
                                'src',
                                'renderer',
                                'src',
                                'assets',
                                'iconfont.js'
                            );
                            const destPath = join(
                                __dirname,
                                '..',
                                'web-static',
                                'src',
                                'assets',
                                'iconfont.js'
                            );
                            fs.ensureFileSync(destPath);
                            fs.copyFileSync(srcPath, destPath);
                            console.log(
                                'Copied iconfont.js to web-static/src/assets/'
                            );
                        },
                    },
                ],
            },
        };
    }

    return {
        main: {
            plugins: [externalizeDepsPlugin()],
            build: {
                rollupOptions: {
                    external: ['minimist', 'electron'],
                },
            },
        },
        preload: {
            plugins: [externalizeDepsPlugin()],
        },
        renderer: {
            ...sharedConfig,
            server: {
                hmr: true,
            },
            plugins: [
                ...sharedConfig.plugins,
                {
                    name: 'copy-iconfont',
                    writeBundle() {
                        const srcPath = join(
                            __dirname,
                            'src',
                            'renderer',
                            'src',
                            'assets',
                            'iconfont.js'
                        );
                        const destDir = join(
                            __dirname,
                            'out',
                            'renderer',
                            'src',
                            'assets'
                        );
                        const destPath = join(destDir, 'iconfont.js');



                        if (fs.existsSync(srcPath)) {
                            console.log('Source file exists');
                        } else {
                            console.log('Source file does not exist');
                        }

                        fs.ensureDirSync(destDir);
                        fs.copyFileSync(srcPath, destPath);
                        console.log(
                            'Copied iconfont.js to out/renderer/src/assets/'
                        );
                    },
                },
            ],
        },
    };
});
