# dingo

Dingo is a desktop application based on Electron and React for visualizing data evaluation results. It supports building both SPA web applications and desktop applications simultaneously.

## Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

## Project Setup

### Install

```bash
$ npm install
```

### Development

```bash
$ npm run dev
```

### Build

```bash
# For Windows
$ npm run build:win

# For macOS
$ npm run build:mac

# Build macOS version (x64 architecture)
$ npm run build:mac-x64

# For Linux
$ npm run build:linux
```

### Start Visualization Web with Dingo CLI

```bash
# Technical approach: build:web ---> web-static/index.html --> execute cli --> visualization web
npm run build:web
After ensuring dingo dependencies are installed, return to the dingo root directory. If there are build artifacts in the root directory, you can proceed without relying on node.
$ python -m dingo.run.vsl --input /path/to/your/input/directory #launch web

With node environment installed, execute
$ npm run dev
python -m dingo.run.vsl --input /path/to/your/input/directory --mode app #launch dingo app
```

### Comparison between CLI Visualization Web and Dingo Desktop Application

```bash
CLI Visualization Web: Data is injected once by default when executing the CLI, doesn't support changing local directory, requires re-execution of CLI
Dingo Desktop Application: No data injection by default, supports adding & changing local directory, supports data visualization
```

### Development Scripts

```bash
# Format code
$ npm run format

# Code linting
$ npm run lint

# Type checking
$ npm run typecheck

# Start the application (preview mode)
$ npm run dev
```

This command runs the application in preview mode. It starts the Electron application using electron-vite with built files, allowing you to test the application as it would run in production, but without packaging.

```bash
# Build Web version
$ npm run build:web
```

This command builds the application for web deployment. It uses electron-vite to build the project, but with configurations specifically adjusted for web output. This allows you to deploy your Electron application as a web application, which is useful for creating web versions of desktop applications.

```bash
# Serve Web build
$ npm run serve:web

# Build and unpack
$ npm run build:unpack
```

### Other Useful Commands

```bash
# Start using npx
$ npm run start-npx

# Run postinstall script
$ npm run postinstall
```
