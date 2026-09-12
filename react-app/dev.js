// dev.js
import ngrok from '@ngrok/ngrok';
import { spawn } from 'node:child_process';

const PORT = 5173;

(async function () {
  let listener;

  try {
    listener = await ngrok.forward({
      addr: PORT,
      authtoken_from_env: true,
    });

    const url = listener.url();
    const hostname = new URL(url).hostname;

    console.log(`✅ ngrok tunnel started at: ${url}`);

    const vite = spawn(
      'vite',
      [
        '--host',
        '0.0.0.0',
        '--config',
        'vite.config.js',
      ],
      {
        stdio: 'inherit',
        shell: true,
        env: {
          ...process.env,
          NGROK_HOSTNAME: hostname,
        },
      },
    );

    vite.on('exit', async (code) => {
      console.log('❌ Vite server stopped. Disconnecting ngrok...');
      await listener.close();
      process.exit(code ?? 0);
    });
  } catch (err) {
    console.error('Failed to start ngrok or Vite:', err);

    if (listener) {
      await listener.close();
    }

    process.exit(1);
  }
})();