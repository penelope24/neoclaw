const { Client, LocalAuth } = require('whatsapp-web.js');
const axios = require('axios');
const qrcode = require('qrcode-terminal');

const PYTHON_URL = 'http://localhost:8000/message';
const DEBUG = process.env.DEBUG === '1';

const log = {
    debug: (...args) => DEBUG && console.log('[DEBUG]', ...args),
    info: (...args) => console.log(...args),
    error: (...args) => console.error('[错误]', ...args),
};

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    }
});

client.on('qr', (qr) => {
    log.info('请用 WhatsApp 扫描以下二维码登录：');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => log.info('✅ 登录成功'));
client.on('ready', () => log.info('✅ WhatsApp 客户端就绪，开始监听消息'));

client.on('message', async (msg) => {
    log.debug(`from=${msg.from} fromMe=${msg.fromMe} body=${msg.body}`);

    if (msg.fromMe) return;
    if (!msg.from.endsWith('@c.us')) return;
    if (!msg.body) return;

    log.info(`[收到] ${msg.from}: ${msg.body}`);

    try {
        const response = await axios.post(PYTHON_URL, {
            sender: msg.from,
            message: msg.body,
        }, { timeout: 120000 });

        const reply = response.data.reply;
        log.info(`[回复] ${reply}`);
        await client.sendMessage(msg.from, reply);

    } catch (err) {
        log.error(err.message);
    }
});

client.on('disconnected', (reason) => log.info('⚠️  WhatsApp 连接断开：', reason));

client.initialize();