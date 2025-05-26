# How to setup?

### Move into plugin dir
```sh
cd mus-vscode-plugin
```
### Install plugin packages
```sh
npm i --force
```
### Compiling..
```sh
npm run compile
npm i -g @vscode/vsce
vsce package
```
### Finally
Use `Ctrl+Shift+P` and write `>` and write `install from vsix` and select the file was created btw file name could be `mus-language-0.2.0.vsix`
