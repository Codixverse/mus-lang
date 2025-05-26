import {
    createConnection,
    TextDocuments,
    ProposedFeatures,
    InitializeParams,
    DidChangeConfigurationNotification,
    CompletionItem,
    CompletionItemKind,
    TextDocumentPositionParams,
    TextDocumentSyncKind,
    InitializeResult,
    Hover,
    MarkupContent,
    MarkupKind,
    SignatureHelp,
    SignatureInformation,
    ParameterInformation
} from 'vscode-languageserver/node';

import {
    TextDocument
} from 'vscode-languageserver-textdocument';

// Create a connection for the server
const connection = createConnection(ProposedFeatures.all);

// Create a text document manager
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

// Keywords for Mus language with descriptions
const keywords = new Map<string, string>([
    ['if', 'Conditional statement'],
    ['else', 'Alternative branch of conditional statement'],
    ['elif', 'Else-if branch of conditional statement'],
    ['while', 'While loop statement'],
    ['for', 'For loop statement'],
    ['in', 'Used in for loops to iterate over collections'],
    ['return', 'Return statement for functions'],
    ['break', 'Break out of a loop'],
    ['continue', 'Skip to next iteration of a loop'],
    ['var', 'Variable declaration'],
    ['const', 'Constant declaration'],
    ['fun', 'Function declaration'],
    ['class', 'Class declaration'],
    ['interface', 'Interface declaration'],
    ['type', 'Type declaration'],
    ['enum', 'Enumeration declaration'],
    ['and', 'Logical AND operator'],
    ['or', 'Logical OR operator'],
    ['not', 'Logical NOT operator'],
    ['is', 'Type check operator'],
    ['as', 'Type cast operator'],
    ['static', 'Static member declaration'],
    ['private', 'Private access modifier'],
    ['public', 'Public access modifier'],
    ['protected', 'Protected access modifier'],
    ['import', 'Import declaration'],
    ['from', 'Import source specifier']
]);

// Built-in functions with signatures and descriptions
const builtInFunctions = new Map<string, { signature: string, description: string }>([
    ['out', { 
        signature: 'out(value: any): void',
        description: 'Outputs a value to the console'
    }],
    ['error', {
        signature: 'error(message: string): void',
        description: 'Outputs an error message'
    }],
    ['warn', {
        signature: 'warn(message: string): void',
        description: 'Outputs a warning message'
    }]
]);

// Types with descriptions
const types = new Map<string, string>([
    ['string', 'Text type'],
    ['integer', 'Integer number type'],
    ['boolean', 'Boolean type (true/false)'],
    ['array', 'Array type (use with generics, e.g., array<integer>)'],
    ['void', 'No return value'],
    ['any', 'Any type'],
    ['number', 'Floating-point number type'],
    ['float', 'Floating-point number type'],
    ['double', 'Double-precision floating-point number type'],
    ['char', 'Single character type'],
    ['byte', '8-bit integer type'],
    ['short', '16-bit integer type'],
    ['long', '64-bit integer type'],
    ['object', 'Object type'],
    ['dynamic', 'Dynamic type'],
    ['never', 'Never type'],
    ['unknown', 'Unknown type'],
    ['color', 'Color type'],
    ['rgb', 'RGB color type'],
    ['rgba', 'RGBA color type'],
    ['hex', 'Hexadecimal color type']
]);

// Add color constants
const colorConstants = new Map<string, string>([
    ['red', '#FF0000'],
    ['green', '#00FF00'],
    ['blue', '#0000FF'],
    ['yellow', '#FFFF00'],
    ['cyan', '#00FFFF'],
    ['magenta', '#FF00FF'],
    ['black', '#000000'],
    ['white', '#FFFFFF'],
    ['gray', '#808080']
]);

// Data structure to hold symbols (variables, functions, classes) per document
interface DocumentSymbols {
    variables: CompletionItem[];
    functions: CompletionItem[];
    classes: CompletionItem[];
}

const documentSymbols: Map<string, DocumentSymbols> = new Map();

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;
let hasDiagnosticRelatedInformationCapability = false;

connection.onInitialize((params: InitializeParams) => {
    const capabilities = params.capabilities;

    hasConfigurationCapability = !!(
        capabilities.workspace && !!capabilities.workspace.configuration
    );
    hasWorkspaceFolderCapability = !!(
        capabilities.workspace && !!capabilities.workspace.workspaceFolders
    );
    hasDiagnosticRelatedInformationCapability = !!(
        capabilities.textDocument &&
        capabilities.textDocument.publishDiagnostics &&
        capabilities.textDocument.publishDiagnostics.relatedInformation
    );

    const result: InitializeResult = {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            completionProvider: {
                resolveProvider: true,
                triggerCharacters: ['.', '>', '(']
            },
            hoverProvider: true,
            signatureHelpProvider: {
                triggerCharacters: ['(', ','],
                retriggerCharacters: [',']
            }
        }
    };

    if (hasWorkspaceFolderCapability) {
        result.capabilities.workspace = {
            workspaceFolders: {
                supported: true
            }
        };
    }

    return result;
});

connection.onInitialized(() => {
    if (hasConfigurationCapability) {
        connection.client.register(DidChangeConfigurationNotification.type, undefined);
    }
});

// Provide code completion
connection.onCompletion((params: TextDocumentPositionParams): CompletionItem[] => {
    const document = documents.get(params.textDocument.uri);
    if (!document) return [];

    const text = document.getText();
    const position = params.position;
    const offset = document.offsetAt(position);
    const line = text.substring(0, offset).split('\n').pop() || '';

    const completions: CompletionItem[] = [];

    // Add document symbols
    const symbols = documentSymbols.get(params.textDocument.uri);
    if (symbols) {
        completions.push(...symbols.variables);
        completions.push(...symbols.functions);
        completions.push(...symbols.classes);
    }

    // Add keywords with descriptions
    keywords.forEach((description, keyword) => {
        completions.push({
            label: keyword,
            kind: CompletionItemKind.Keyword,
            detail: description,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `**${keyword}** - ${description}`
            }
        });
    });

    // Add types with descriptions
    types.forEach((description, type) => {
        completions.push({
            label: type,
            kind: CompletionItemKind.TypeParameter,
            detail: description,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `**${type}** - ${description}`
            }
        });
    });

    // Add color constants
    colorConstants.forEach((value, color) => {
        completions.push({
            label: color,
            kind: CompletionItemKind.Color,
            detail: `Color: ${value}`,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `**${color}**\n\nHex value: \`${value}\``
            },
            data: 'color'
        });
    });

    // Add built-in functions with signatures and descriptions
    builtInFunctions.forEach((info, func) => {
        completions.push({
            label: func,
            kind: CompletionItemKind.Function,
            detail: info.signature,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `**${func}**\n\n${info.signature}\n\n${info.description}`
            }
        });
    });

    return completions;
});

// Provide hover information
connection.onHover((params: TextDocumentPositionParams): Hover | null => {
    const document = documents.get(params.textDocument.uri);
    if (!document) return null;

    const text = document.getText();
    const position = params.position;
    const offset = document.offsetAt(position);
    const word = getWordAtOffset(text, offset);

    if (!word) return null;

    // Check keywords
    if (keywords.has(word)) {
        return {
            contents: {
                kind: MarkupKind.Markdown,
                value: `**${word}** - ${keywords.get(word)}`
            }
        };
    }

    // Check types
    if (types.has(word)) {
        return {
            contents: {
                kind: MarkupKind.Markdown,
                value: `**${word}** - ${types.get(word)}`
            }
        };
    }

    // Check built-in functions
    if (builtInFunctions.has(word)) {
        const info = builtInFunctions.get(word)!;
        return {
            contents: {
                kind: MarkupKind.Markdown,
                value: `**${word}**\n\n${info.signature}\n\n${info.description}`
            }
        };
    }

    // Check document symbols
    const symbols = documentSymbols.get(params.textDocument.uri);
    if (symbols) {
        const variable = symbols.variables.find(v => v.label === word);
        if (variable) {
            return {
                contents: {
                    kind: MarkupKind.Markdown,
                    value: `**${word}** - ${variable.detail}`
                }
            };
        }

        const func = symbols.functions.find(f => f.label === word);
        if (func) {
            return {
                contents: {
                    kind: MarkupKind.Markdown,
                    value: `**${word}** - ${func.detail}`
                }
            };
        }
    }

    return null;
});

// Provide signature help
connection.onSignatureHelp((params: TextDocumentPositionParams): SignatureHelp | null => {
    const document = documents.get(params.textDocument.uri);
    if (!document) return null;

    const text = document.getText();
    const position = params.position;
    const offset = document.offsetAt(position);
    const line = text.substring(0, offset).split('\n').pop() || '';

    // Find the function name before the current position
    const functionMatch = line.match(/(\w+)\s*\(/);
    if (!functionMatch) return null;

    const functionName = functionMatch[1];

    // Check built-in functions
    if (builtInFunctions.has(functionName)) {
        const info = builtInFunctions.get(functionName)!;
        const signature = SignatureInformation.create(
            info.signature,
            info.description
        );

        // Parse parameters from signature
        const paramMatch = info.signature.match(/\((.*)\)/);
        if (paramMatch) {
            const params = paramMatch[1].split(',').map(param => {
                const [name, type] = param.trim().split(':').map(s => s.trim());
                return ParameterInformation.create(
                    param.trim(),
                    `Parameter ${name} of type ${type}`
                );
            });
            signature.parameters = params;
        }

        return {
            signatures: [signature],
            activeSignature: 0,
            activeParameter: getActiveParameter(line)
        };
    }

    // Check document functions
    const symbols = documentSymbols.get(params.textDocument.uri);
    if (symbols) {
        const func = symbols.functions.find(f => f.label === functionName);
        if (func) {
            const signature = SignatureInformation.create(
                func.detail || functionName,
                func.documentation?.toString()
            );

            return {
                signatures: [signature],
                activeSignature: 0,
                activeParameter: getActiveParameter(line)
            };
        }
    }

    return null;
});

// Helper function to get the word at a given offset
function getWordAtOffset(text: string, offset: number): string | null {
    const beforeOffset = text.substring(0, offset);
    const afterOffset = text.substring(offset);
    const wordBefore = beforeOffset.match(/[\w\d_]+$/)?.[0] || '';
    const wordAfter = afterOffset.match(/^[\w\d_]+/)?.[0] || '';
    return wordBefore + wordAfter || null;
}

// Helper function to get the active parameter index
function getActiveParameter(line: string): number {
    const match = line.match(/\((.*)/);
    if (!match) return 0;

    const args = match[1];
    return args.split(',').length - 1;
}

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
    const text = textDocument.getText();
    const uri = textDocument.uri;

    const variables: CompletionItem[] = [];
    const functions: CompletionItem[] = [];
    const classes: CompletionItem[] = [];

    // Find variable declarations
    const variableRegex = /\b(var|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=>\s*([a-zA-Z_][a-zA-Z0-9_<>]*)\s*=/g;
    let varMatch;
    while ((varMatch = variableRegex.exec(text)) !== null) {
        const varName = varMatch[2];
        const varType = varMatch[3];
        variables.push({
            label: varName,
            kind: CompletionItemKind.Variable,
            detail: `(${varType}) ${varName}`,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `Variable **${varName}** of type \`${varType}\``
            }
        });
    }

    // Find function declarations
    const functionRegex = /\bfun\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)/g;
    let funcMatch;
    while ((funcMatch = functionRegex.exec(text)) !== null) {
        const funcName = funcMatch[1];
        const params = funcMatch[2];
        functions.push({
            label: funcName,
            kind: CompletionItemKind.Function,
            detail: `fun ${funcName}(${params})`,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `Function **${funcName}**\n\nParameters: ${params}`
            }
        });
    }

    // Find class declarations
    const classRegex = /\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)/g;
    let classMatch;
    while ((classMatch = classRegex.exec(text)) !== null) {
        const className = classMatch[1];
        classes.push({
            label: className,
            kind: CompletionItemKind.Class,
            detail: `class ${className}`,
            documentation: {
                kind: MarkupKind.Markdown,
                value: `Class **${className}**`
            }
        });
    }

    // Store the symbols for this document
    documentSymbols.set(uri, { variables, functions, classes });
}

// Listen for text document changes
documents.onDidChangeContent(change => {
    validateTextDocument(change.document);
});

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();

// Add completion resolve handler
connection.onCompletionResolve((item: CompletionItem): CompletionItem => {
    // Add more details to the completion item if needed
    if (item.data === 'color') {
        const colorValue = colorConstants.get(item.label.toString());
        if (colorValue) {
            item.detail = `Color: ${colorValue}`;
            item.documentation = {
                kind: MarkupKind.Markdown,
                value: `**${item.label}**\n\nHex value: \`${colorValue}\``
            };
        }
    }
    return item;
}); 