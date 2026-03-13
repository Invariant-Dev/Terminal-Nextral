/**
 * Nextral WhatsApp Bridge — whatsapp-web.js + JSON-RPC over stdin/stdout
 * 
 * Communicates with the Python backend via JSON lines on stdin/stdout.
 * Commands are sent as JSON objects, responses are returned as JSON objects.
 * 
 * Protocol:
 *   -> {"action":"status"}
 *   <- {"ok":true,"status":"ready","info":{"name":"...","number":"..."}}
 * 
 *   -> {"action":"get_chats","limit":20}
 *   <- {"ok":true,"chats":[{"id":"...","name":"...","unread":0,"lastMsg":"...","timestamp":...}]}
 * 
 *   -> {"action":"get_messages","chatId":"...","limit":20}
 *   <- {"ok":true,"messages":[{"from":"...","body":"...","timestamp":...,"fromMe":false}]}
 * 
 *   -> {"action":"send_message","chatId":"...","body":"Hello"}
 *   <- {"ok":true,"messageId":"..."}
 * 
 *   -> {"action":"search_contacts","query":"John"}
 *   <- {"ok":true,"contacts":[{"id":"...","name":"...","number":"..."}]}
 * 
 *   -> {"action":"qr_status"}
 *   <- {"ok":true,"authenticated":true/false,"qr":"base64..."}
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const readline = require('readline');
const path = require('path');

// ── State ────────────────────────────────────────────────────────────────
let clientReady = false;
let lastQR = null;
let clientInfo = null;

// ── Client Setup ─────────────────────────────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: path.join(__dirname, '.wwebjs_auth')
    }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    }
});

function respond(obj) {
    process.stdout.write(JSON.stringify(obj) + '\n');
}

function respondError(msg) {
    respond({ ok: false, error: msg });
}

// ── Events ───────────────────────────────────────────────────────────────
client.on('qr', (qr) => {
    lastQR = qr;
    debugLog('QR code received');
    qrcode.generate(qr, { small: true }, (qrText) => {
        // Send QR as event
        respond({ event: 'qr', qr: qr, qrText: qrText });
    });
});

client.on('loading_screen', (percent, message) => {
    debugLog(`Loading: ${percent}% - ${message}`);
    respond({ event: 'loading', percent, message });
});

client.on('ready', () => {
    clientReady = true;
    clientInfo = client.info;
    debugLog('Client is ready!');
    respond({
        event: 'ready',
        info: {
            name: clientInfo?.pushname || 'Unknown',
            number: clientInfo?.wid?.user || 'Unknown'
        }
    });
});

client.on('authenticated', () => {
    debugLog('Authenticated successfully');
    respond({ event: 'authenticated' });
});

client.on('auth_failure', (msg) => {
    debugLog(`Authentication failure: ${msg}`);
    respond({ event: 'auth_failure', message: msg });
});

client.on('change_state', (state) => {
    debugLog(`State changed: ${state}`);
    respond({ event: 'state_change', state: state });
});

client.on('disconnected', (reason) => {
    clientReady = false;
    debugLog(`Disconnected: ${reason}`);
    respond({ event: 'disconnected', reason: reason });
});

client.on('message', (msg) => {
    // Notify Python about incoming messages
    respond({
        event: 'message',
        from: msg.from,
        body: msg.body,
        timestamp: msg.timestamp,
        fromMe: msg.fromMe,
        chatName: msg._data?.notifyName || msg.from
    });
});

// ── Command Handler ──────────────────────────────────────────────────────
async function handleCommand(cmd) {
    debugLog(`Handling command: ${cmd.action}`);
    try {
        switch (cmd.action) {
            case 'status': {
                respond({
                    ok: true,
                    status: clientReady ? 'ready' : 'connecting',
                    authenticated: clientReady,
                    info: clientReady ? {
                        name: clientInfo?.pushname || 'Unknown',
                        number: clientInfo?.wid?.user || 'Unknown'
                    } : null
                });
                break;
            }

            case 'qr_status': {
                respond({
                    ok: true,
                    authenticated: clientReady,
                    qr: lastQR || null
                });
                break;
            }

            case 'get_chats': {
                if (!clientReady) { respondError('WhatsApp client is not ready. Please scan the QR code first.'); break; }
                const limit = cmd.limit || 20;
                debugLog(`Fetching ${limit} chats...`);
                const chats = await client.getChats();
                const result = chats.slice(0, limit).map(c => ({
                    id: c.id._serialized,
                    name: c.name || c.id.user || 'Unknown',
                    unread: c.unreadCount || 0,
                    lastMsg: c.lastMessage?.body?.substring(0, 100) || '',
                    timestamp: c.lastMessage?.timestamp || 0,
                    isGroup: c.isGroup
                }));
                respond({ ok: true, chats: result });
                break;
            }

            case 'get_messages': {
                if (!clientReady) { respondError('WhatsApp client is not ready.'); break; }
                const chatId = cmd.chatId;
                if (!chatId) { respondError('Missing chatId for get_messages'); break; }
                debugLog(`Fetching messages for ${chatId}...`);
                const chat = await client.getChatById(chatId);
                const limit = cmd.limit || 20;
                const messages = await chat.fetchMessages({ limit });
                const result = messages.map(m => ({
                    id: m.id._serialized,
                    from: m._data?.notifyName || m.from,
                    body: m.body,
                    timestamp: m.timestamp,
                    fromMe: m.fromMe,
                    type: m.type
                }));
                respond({ ok: true, messages: result });
                break;
            }

            case 'send_message': {
                if (!clientReady) { respondError('WhatsApp client is not ready.'); break; }
                const { chatId, body } = cmd;
                if (!chatId || !body) { respondError('Missing chatId or body for send_message'); break; }
                debugLog(`Sending message to ${chatId}...`);
                const sentMsg = await client.sendMessage(chatId, body);
                respond({ ok: true, messageId: sentMsg.id._serialized });
                break;
            }

            case 'search_contacts': {
                if (!clientReady) { respondError('WhatsApp client is not ready.'); break; }
                const query = (cmd.query || '').toLowerCase();
                debugLog(`Searching contacts with query: ${query}`);
                const contacts = await client.getContacts();
                const filtered = contacts
                    .filter(c => (c.name && c.name.toLowerCase().includes(query)) || (c.id.user && c.id.user.includes(query)))
                    .slice(0, 20)
                    .map(c => ({
                        id: c.id._serialized,
                        name: c.name || c.id.user || 'Unknown',
                        number: c.id.user || 'Unknown',
                        isGroup: c.isGroup || false
                    }));
                respond({ ok: true, contacts: filtered });
                break;
            }

            case 'logout': {
                debugLog('Logging out...');
                if (clientReady) {
                    await client.logout();
                    clientReady = false;
                }
                respond({ ok: true });
                break;
            }

            case 'shutdown': {
                debugLog('Shutting down...');
                respond({ ok: true });
                process.exit(0);
                break;
            }

            default:
                debugLog(`Unknown action requested: ${cmd.action}`);
                respondError(`Unknown action: ${cmd.action}`);
        }
    } catch (err) {
        debugLog(`ERROR in handleCommand (${cmd.action}): ${err.stack || err.message}`);
        respondError(`Bridge internal error during ${cmd.action}: ${err.message}`);
    }
}

// ── Helpers ─────────────────────────────────────────────────────────────
function respond(obj) {
    process.stdout.write(JSON.stringify(obj) + '\n');
}

function respondError(msg) {
    respond({ ok: false, error: msg });
}

function debugLog(msg) {
    process.stderr.write(`[DEBUG] ${new Date().toISOString()} - ${msg}\n`);
}

// ── stdin listener ───────────────────────────────────────────────────────
const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', (line) => {
    if (!line.trim()) return;
    try {
        const cmd = JSON.parse(line.trim());
        handleCommand(cmd);
    } catch (e) {
        debugLog(`Failed to parse stdin JSON: ${line}`);
        respondError(`Invalid command JSON: ${e.message}`);
    }
});

// ── Start ────────────────────────────────────────────────────────────────
debugLog('Initializing WhatsApp client...');
respond({ event: 'starting', message: 'WhatsApp bridge initializing...' });

client.initialize().catch(err => {
    debugLog(`CRITICAL: Bridge failed to initialize: ${err.stack || err.message}`);
    respond({ event: 'error', message: `Initialization failed: ${err.message}` });
});
